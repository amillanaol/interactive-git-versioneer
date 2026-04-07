# Configuración de IA

| Necesidad | Ubicación |
| :--- | :--- |
| Configurar proveedor desde menú | `igv` → Configure AI (opción 2) |
| Configurar desde CLI | `igv config set OPENAI.*` |
| Quick setup Groq | Opción 4 en menú Configure AI |
| Quick setup OpenRouter | Opción 5 en menú Configure AI |
| Seleccionar modelo con lista en vivo | Opción 3 en menú Configure AI |
| Ver proveedor activo y modelos disponibles | `igv` → Show current configuration (opción 1) |

## Proveedores Soportados

| Proveedor | Base URL | Modelo por defecto |
| :--- | :--- | :--- |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Custom | Cualquier URL OpenAI-compatible | Según proveedor |

## Claves de Configuración

| Clave | Descripción | Archivo |
| :--- | :--- | :--- |
| `OPENAI.key` | API key del proveedor | `~/.igv/config.json` |
| `OPENAI.baseURL` | URL base del endpoint | `~/.igv/config.json` |
| `OPENAI.model` | Identificador del modelo | `~/.igv/config.json` |

## Configuración Rápida

**Groq** — obtener key en `https://console.groq.com/keys`

```bash
igv config set OPENAI.key "gsk_your_api_key"
igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"
igv config set OPENAI.model "llama-3.3-70b-versatile"
```

**OpenRouter** — obtener key en `https://openrouter.ai/keys`

```bash
igv config set OPENAI.key "sk-or-v1-your_api_key"
igv config set OPENAI.baseURL "https://openrouter.ai/api/v1"
igv config set OPENAI.model "meta-llama/llama-3.3-70b-instruct"
```

## Selector de Modelos en Vivo (opción 3)

Al elegir opción 3 en Configure AI, IGV consulta el endpoint `/models` del proveedor configurado y presenta una lista paginada (10 modelos/página) con las siguientes columnas:

| Columna | Fuente | Notas |
| :--- | :--- | :--- |
| Model | `model.id` | Truncado a 45 chars si es más largo |
| Context | `model_extra.context_window` / `context_length` | Formateado como `8K`, `128K`, `1M` |
| Provider | `model.owned_by` | Truncado a 14 chars |
| Free | Ver lógica en [`modules/core_ai.md`](../modules/core_ai.md) | `Yes` / `No` / `-` |

El modelo actualmente configurado aparece marcado con `→`. Navegar con `n` (siguiente), `p` (anterior). Opción `m` permite escribir un ID manualmente. Si la llamada a la API falla, cae a un prompt de texto manual.

## Información de Free Tier en Groq

La columna Free para modelos Groq se resuelve contra `_GROQ_FREE_MODELS` en `core/ai.py`. Fuente: `https://console.groq.com/docs/rate-limits` (2026-02-25). Modelos ausentes del frozenset requieren plan Developer o superior.

## Pantalla "Show current configuration"

La opción 1 del menú Config muestra un bloque de resumen derivado antes del volcado del JSON:

| Campo mostrado | Valor |
| :--- | :--- |
| Proveedor actual | Detectado desde `OPENAI.baseURL` vía `_detect_provider()` |
| Proveedores disponibles | Lista estática: Groq, OpenRouter, OpenAI, Custom |
| Modelo activo | Valor de `OPENAI.model`; omitido si no está configurado |

## Arquitectura

La integración sigue el patrón Ports & Adapters. El puerto abstracto define el contrato; el adaptador provee la implementación concreta.

| Componente | Archivo | Rol |
| :--- | :--- | :--- |
| `AiService` (puerto) | `domain/services/ai_service.py` | Interfaz abstracta |
| `OpenAiCompatibleAdapter` | `core/ai.py` | Implementación concreta |
| `get_ai_service()` | `core/ai.py` | Factory: lee config y retorna adaptador |
| `list_available_models()` | `core/ai.py` | Consulta `/models` del proveedor configurado |
| `_GROQ_FREE_MODELS` | `core/ai.py` | Frozenset de modelos gratuitos de Groq |
| `_detect_provider()` | `config/menu.py` | Infiere nombre del proveedor desde la URL |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-25 |
