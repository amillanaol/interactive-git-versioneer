# Core: AI Adapter

| Necesidad | Ubicación |
| :--- | :--- |
| Generar mensaje de tag con IA | `core/ai.py:generate_tag_message()` |
| Clasificar tipo de versión con IA | `core/ai.py:determine_version_type()` |
| Obtener servicio configurado | `core/ai.py:get_ai_service()` |
| Listar modelos del proveedor con metadata | `core/ai.py:list_available_models()` |
| Puerto abstracto (interfaz) | `domain/services/ai_service.py:AiService` |

## API Pública

| Símbolo | Tipo | Descripción |
| :--- | :--- | :--- |
| `OpenAiCompatibleAdapter` | clase | Implementa `AiService`; compatible con OpenAI, Groq, OpenRouter |
| `get_ai_service()` | función | Factory: lee `~/.igv/config.json` y retorna adaptador configurado |
| `generate_tag_message(...)` | función | Wrapper backward-compat; delega a `get_ai_service()` |
| `determine_version_type(...)` | función | Wrapper backward-compat; delega a `get_ai_service()` |
| `list_available_models()` | función | Fetches `/models` del proveedor configurado; retorna lista con metadata |
| `_GROQ_FREE_MODELS` | `FrozenSet[str]` | Conjunto de model IDs disponibles en el plan gratuito de Groq |

## `OpenAiCompatibleAdapter`

Constructor: `OpenAiCompatibleAdapter(api_key, base_url, model)`

| Método | Firma | Retorno |
| :--- | :--- | :--- |
| `generate_tag_message` | `(commit_message, commit_diff, version_type, max_length=72, locale="es")` | `Optional[str]` |
| `determine_version_type` | `(commit_message, commit_diff)` | `Tuple[str, str]` — (tipo, razón) |

## `list_available_models()`

Lee `OPENAI.key` y `OPENAI.baseURL` desde config y llama al endpoint `/models` del proveedor. Retorna lista vacía ante cualquier error de red o configuración incompleta.

Estructura de cada elemento retornado:

| Campo | Tipo | Fuente |
| :--- | :--- | :--- |
| `id` | `str` | `model.id` |
| `context_window` | `Optional[int]` | `model_extra.context_window` (Groq) o `model_extra.context_length` (OpenRouter) |
| `owned_by` | `str` | `model.owned_by` |
| `is_free` | `Optional[bool]` | Ver tabla de detección abajo |

Lógica de detección de `is_free`:

| Condición evaluada (en orden) | Resultado |
| :--- | :--- |
| `model_extra.pricing.prompt == "0"` y `pricing.completion == "0"` | `True` |
| `model_extra.pricing.prompt` o `completion` distinto de `"0"` | `False` |
| `model.id` termina en `:free` | `True` |
| Proveedor es Groq (`groq.com` en URL) y `id` está en `_GROQ_FREE_MODELS` | `True` |
| Proveedor es Groq y `id` NO está en `_GROQ_FREE_MODELS` | `False` |
| Ninguna condición aplica | `None` (desconocido) |

## `_GROQ_FREE_MODELS`

Fuente: `https://console.groq.com/docs/rate-limits` (consultado 2026-02-25). Contiene los model IDs disponibles en el plan Free de Groq. Actualizar manualmente cuando Groq modifique su página de rate limits.

## Uso

```python
from interactive_git_versioneer.core.ai import get_ai_service, list_available_models

service = get_ai_service()  # Lee config de ~/.igv/config.json
vtype, reason = service.determine_version_type("Add feature X", "diff...")
msg = service.generate_tag_message("Add feature X", "diff...", vtype)

models = list_available_models()  # [{"id": ..., "context_window": ..., "is_free": ...}]
```

Uso directo con constructor (pruebas / inyección):

```python
from interactive_git_versioneer.core.ai import OpenAiCompatibleAdapter

adapter = OpenAiCompatibleAdapter(
    api_key="sk-or-v1-...",
    base_url="https://openrouter.ai/api/v1",
    model="meta-llama/llama-3.3-70b-instruct",
)
```

## Requisitos

`OPENAI.key` y `OPENAI.baseURL` configurados en `~/.igv/config.json`. Librería `openai>=1.0.0` instalada.

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-25 |
