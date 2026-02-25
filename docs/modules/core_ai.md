# Core: AI Adapter

| Necesidad | Ubicación |
| :--- | :--- |
| Generar mensaje de tag con IA | `core/ai.py:generate_tag_message()` |
| Clasificar tipo de versión con IA | `core/ai.py:determine_version_type()` |
| Obtener servicio configurado | `core/ai.py:get_ai_service()` |
| Puerto abstracto (interfaz) | `domain/services/ai_service.py:AiService` |

## API Pública

| Símbolo | Tipo | Descripción |
| :--- | :--- | :--- |
| `OpenAiCompatibleAdapter` | clase | Implementa `AiService`; compatible con OpenAI, Groq, OpenRouter |
| `get_ai_service()` | función | Factory: lee `~/.igv/config.json` y retorna adaptador configurado |
| `generate_tag_message(...)` | función | Wrapper backward-compat; delega a `get_ai_service()` |
| `determine_version_type(...)` | función | Wrapper backward-compat; delega a `get_ai_service()` |

## `OpenAiCompatibleAdapter`

Constructor: `OpenAiCompatibleAdapter(api_key, base_url, model)`

| Método | Firma | Retorno |
| :--- | :--- | :--- |
| `generate_tag_message` | `(commit_message, commit_diff, version_type, max_length=72, locale="es")` | `Optional[str]` |
| `determine_version_type` | `(commit_message, commit_diff)` | `Tuple[str, str]` — (tipo, razón) |

## Uso

```python
from interactive_git_versioneer.core.ai import get_ai_service

service = get_ai_service()  # Lee config de ~/.igv/config.json
vtype, reason = service.determine_version_type("Add feature X", "diff...")
msg = service.generate_tag_message("Add feature X", "diff...", vtype)
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
