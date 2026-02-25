# Configuración de IA

| Necesidad | Ubicación |
| :--- | :--- |
| Configurar proveedor desde menú | `igv` → Configure AI (opción 2) |
| Configurar desde CLI | `igv config set OPENAI.*` |
| Quick setup Groq | Opción 4 en menú Configure AI |
| Quick setup OpenRouter | Opción 5 en menú Configure AI |
| Ver proveedor activo | Estado visible en menú Config |

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

## Modelos Recomendados por Proveedor

| Proveedor | Modelo | Uso |
| :--- | :--- | :--- |
| Groq | `llama-3.3-70b-versatile` | Recomendado para Groq |
| Groq | `mixtral-8x7b-32768` | Contexto largo |
| Groq | `gemma2-9b-it` | Alternativa ligera |
| OpenRouter | `meta-llama/llama-3.3-70b-instruct` | Recomendado para OpenRouter |
| OpenRouter | `google/gemini-flash-1.5` | Alta velocidad |
| OpenRouter | `anthropic/claude-3-haiku` | Calidad premium |
| OpenRouter | `openai/gpt-4o-mini` | Equilibrio coste/calidad |

## Arquitectura

La integración sigue el patrón Ports & Adapters. El puerto abstracto define el contrato; el adaptador provee la implementación concreta.

| Componente | Archivo | Rol |
| :--- | :--- | :--- |
| `AiService` (puerto) | `domain/services/ai_service.py` | Interfaz abstracta |
| `OpenAiCompatibleAdapter` | `core/ai.py` | Implementación concreta |
| `get_ai_service()` | `core/ai.py` | Factory: lee config y retorna adaptador |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-25 |
