# Configuración de IA

Proveedores y modelos soportados para generación automática de mensajes.

## Proveedores Soportados

| Proveedor | Base URL | Modelo por defecto |
| :--- | :--- | :--- |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` |

## Configuración Rápida

```bash
igv config set OPENAI.key "gsk_your_api_key"
igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"
igv config set OPENAI.model "llama-3.3-70b-versatile"
```

Implementación: `src/interactive_git_versioneer/core/ai.py:get_openai_client()`

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
