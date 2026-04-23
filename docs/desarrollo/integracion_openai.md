# Integración de IA con Conector OpenAI-Compatible

## Guía Completa para Proyectos Python

Este documento explica cómo Integrated Git Versioneer (IGV) integra servicios de IA usando el patrón **Ports & Adapters** (Hexagonal Architecture). Al final, podrás aplicar estos conceptos a cualquier proyecto Python.

---

## 1. Arquitectura General

El diseño sigue el principio de **inversión de dependencias**: el núcleo de dominio define qué necesita (el "puerto"), y la capa de infraestructura provee cómo implementarlo ("adaptador").

![[Arquitectura General.png]]

---

## 2. El Puerto (Interfaz)

### 2.1 Definición en domain/services/ai_service.py

```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class AiService(ABC):
    """Puerto abstracto para generación de texto con IA.
    
    El dominio define qué necesita; los adaptadores definen cómo.
    """

    @abstractmethod
    def generate_tag_message(
        self,
        commit_message: str,
        commit_diff: str,
        version_type: str,
        max_length: int = 72,
        locale: str = "es",
    ) -> Optional[str]:
        """Genera mensaje de tag desde un commit."""
        pass

    @abstractmethod
    def determine_version_type(
        self,
        commit_message: str,
        commit_diff: str,
    ) -> Tuple[str, str]:
        """Clasifica commit en tipo de versión semántica.
        
        Returns:
            (version_type, reason): ej: ("minor", "Nueva funcionalidad")
        """
        pass
```

### 2.2 Por qué usar ABC?

- **ABC** (Abstract Base Class) fuerza a las subclases a implementar los métodos abstractos
- Si alguien crea un adaptador sin implementar `generate_tag_message()`, Python lanza `TypeError` en tiempo de instanciación
- El código de aplicación soloknows sobre `AiService`, nunca sobre `OpenAiCompatibleAdapter`

---

## 3. El Adaptador (Implementación Concreta)

### 3.1 Estructura básica en core/ai.py

```python
from typing import Any, Optional, Tuple
from ..domain.services.ai_service import AiService


class OpenAiCompatibleAdapter(AiService):
    """Adaptador que usa la librería 'openai' - compatible con cualquier provider
    que siga la spec de OpenAI.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
```

### 3.2 Método para obtener el cliente

```python
    def _get_client(self) -> Any:
        """Lazy loading del cliente OpenAI."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' library is not installed.\n"
                "Install it with: pip install openai"
            )
        return OpenAI(api_key=self._api_key, base_url=self._base_url)
```

**Nota técnica**: El import dentro de la función (no al nivel del módulo) permite:
- Import más rápido al iniciar
- Mejor mensaje de error si la librería no está instalada

### 3.3 Generación de mensajes de tag

```python
    def generate_tag_message(
        self,
        commit_message: str,
        commit_diff: str,
        version_type: str,
        max_length: int = 72,
        locale: str = "es",
    ) -> Optional[str]:
        """Genera mensaje de tag git desde un diff."""
        client = self._get_client()

        # Construir el prompt
        prompt = f"""Genera un mensaje de tag basado en:

Commit: {commit_message}
Diff: {commit_diff}

Tipo: {version_type}
Idioma: {es}
Máx caracteres: {max_length}

Escribe solo el mensaje. Sin explicaciones."""

        # Llamada a la API
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "Eres un generador de mensajes git."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
            stop=["\n\n", "---", "```"],
        )

        # Extraer resultado
        result = response.choices[0].message.content.strip()
        
        # Limpiar respuestas con comillas
        result = result.strip("\"'`")
        
        # Tomar solo primera línea
        if "\n" in result:
            result = result.split("\n")[0]

        return result
```

### 3.4 Clasificación de tipo de versión

```python
    def determine_version_type(
        self,
        commit_message: str,
        commit_diff: str,
    ) -> Tuple[str, str]:
        """Clasifica commit en major/minor/patch."""
        client = self._get_client()

        prompt = f"""Clasifica este commit:

{commit_message}

Diff:
{commit_diff}

Reglas:
- major: cambios incompatibles, cambios de API
- minor: nuevas features (compatibles hacia atrás)
- patch: bug fixes, docs, refactoring menor

Formato exacto (2 líneas):
TYPE: [major|minor|patch]
REASON: [razón en español]"""

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "Clasificador de versiones semánticas."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.2,
        )

        result = response.choices[0].message.content.strip()

        # Parseo defensivo
        version_type = "patch"
        reason = "Cambio menor"

        for line in result.split("\n"):
            line = line.strip().upper()
            if line.startswith("TYPE:"):
                tipo = line.split(":", 1)[1].strip().lower()
                if tipo in ("major", "minor", "patch"):
                    version_type = tipo
            elif line.startswith("REASON:") or line.startswith("RAZÓN:"):
                reason = line.split(":", 1)[1].strip()

        return version_type, reason
```

---

## 4. La Factory get_ai_service()

### 4.1 Propósito

La factory oculta la construcción del adaptador. El código cliente no sabe qué clase concreta usa.

```python
def get_ai_service() -> AiService:
    """Factory: construye AiService desde configuración."""
    # Leer configuración
    api_key = get_config_value("OPENAI.key")
    base_url = get_config_value("OPENAI.baseURL")
    model = get_config_value("OPENAI.model")

    if not base_url:
        raise ValueError("Base URL no configurada")

    if not api_key:
        # ¿Proveedor local como Ollama?
        if _is_local_provider(base_url):
            api_key = "ollama"  # dummy key
        else:
            raise ValueError("API key requerida")

    return OpenAiCompatibleAdapter(
        api_key=api_key,
        base_url=base_url,
        model=model or "llama3.2",
    )
```

### 4.2 Detección de proveedor local

```python
def _is_local_provider(base_url: Optional[str]) -> bool:
    """Detecta si base_url apunta a proveedor local."""
    if not base_url:
        return False
    return "localhost" in base_url or "127.0.0.1" in base_url
```

**Por qué esto importa**:
- Ollama (proveedor local) NO requiere API key real
- La factory inyecta una dummy key automáticamente
- El código cliente no necesita saber si usa Ollama o OpenAI cloud

---

## 5. Providers Soportados

| Proveedor | Base URL | Modelo por defecto |
|----------|--------|-------------------|
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` |
| OpenAI | `https://api.openai.com/v1` | (requiere API key) |
| Ollama | `http://localhost:11434/v1` | `llama3.2` |
| Custom | cualquier URL compatible | configurable |

Todos usan el mismo código de cliente porque implementan la spec de OpenAI.

---

## 6. Uso desde Código Cliente

### 6.1 Con Dependency Injection

```python
# En el menú de tags
from ..core.ai import get_ai_service

def auto_generate_tags():
    service = get_ai_service()
    
    commits = get_untagged_commits()
    for commit in commits:
        # Clasificar tipo de versión
        version_type, reason = service.determine_version_type(
            commit.message,
            commit.diff,
        )
        
        # Generar mensaje de tag
        tag_message = service.generate_tag_message(
            commit.message,
            commit.diff,
            version_type,
        )
        
        # Aplicar tag...
```

### 6.2 Con Funciones Módulo-Level (Backward Compatibility)

```python
# También disponible como funciones sueltas
from ..core.ai import generate_tag_message, determine_version_type

# Estas delegan automáticamente a get_ai_service()
message = generate_tag_message(commit_msg, diff, "minor")
version_type, reason = determine_version_type(commit_msg, diff)
```

---

## 7. Construcción de Prompts

### 7.1 Función auxiliar

```python
def _build_prompt_from_template(...) -> str:
    """Construye prompt desde template o默认值."""
    
    # Intentar cargar template personalizado
    if is_tag:
        template = load_prompt_tags_template()
    else:
        template = load_prompt_template()

    if template:
        try:
            return template.format(
                maxLength=max_length,
                locale=locale,
                type=version_type,
                detailLevel=detail_level,
            ) + f"\n\nOriginal: {commit_message}\n\nDiff:\n{commit_diff}"
        except KeyError:
            pass  # Falls back a default

    # Default prompt...
```

### 7.2 Beneficio de templates

- Templatespersonalizables sin cambiar código
- Permite diferentes estilos de mensajes por proyecto
- Fallback automático si template no existe

---

## 8. Funcionalidades Avanzadas

### 8.1 Listar modelos disponibles

```python
def list_available_models() -> list:
    """Llamar al endpoint /models del provider."""
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.models.list()
    
    return [
        {
            "id": m.id,
            "context_window": getattr(m, "context_window", None),
            "owned_by": getattr(m, "owned_by", ""),
        }
        for m in response.data
    ]
```

### 8.2 Modelos de Ollama (nativo)

```python
def list_ollama_models() -> list:
    """Ollama usa /api/tags (no /v1/models)."""
    base_url = base_url.replace("/v1", "").rstrip("/")
    response = requests.get(f"{base_url}/api/tags")
    
    return [
        {
            "id": m["name"],
            "size": m["size"],
            "modified_at": m["modified_at"],
        }
        for m in response.json()["models"]
    ]
```

---

## 9. Resumen de Arquitectura

![[Resumen de Arquitectura.png]]

---

## 10. Cómo Integrar en Tu Proyecto

### Paso 1: Define el Puerto

```python
# domain/services/ai_service.py
from abc import ABC, abstractmethod

class TuAiService(ABC):
    @abstractmethod
    def generar_resumen(self, texto: str) -> str:
        pass
```

### Paso 2: Implementa el Adaptador

```python
# infrastructure/openai_adapter.py
from openai import OpenAI
from domain.services.ai_service import TuAiService

class TuOpenAIAdapter(TuAiService):
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generar_resumen(self, texto: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": f"Resume: {texto}"}],
        )
        return response.choices[0].message.content
```

### Paso 3: Usa la Factory

```python
# application/tu_modulo.py
def obtener_servicio() -> TuAiService:
    from infrastructure.openai_adapter import TuOpenAIAdapter
    return TuOpenAIAdapter(
        api_key="sk-...",
        base_url="https://api.openai.com/v1",
        model="gpt-4",
    )

def tu_funcion():
    servicio = obtener_servicio()
    resumen = servicio.generar_resumen("Tu texto largo...")
```

---

## 11. Beneficios de Esta Arquitectura

| Beneficio | Descripción |
|----------|-------------|
| **Testabilidad** | Puedes mockear `AiService` en tests |
| **Flexibilidad** | Cambiar provider sin cambiar código de dominio |
| **Separación** | El dominio no depende de librerías externas |
| **Extensibilidad** | Añadir nuevo provider = nueva clase |
| **Mantenibilidad** | Lógica de construcción aislada en factory |

---

## 12. Referencias

- **Código fuente completo**: `src/interactive_git_versioneer/core/ai.py`
- **Puerto**: `src/interactive_git_versioneer/domain/services/ai_service.py`
- **Librería OpenAI Python**: https://github.com/openai/openai-python