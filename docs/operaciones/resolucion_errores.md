# Resolución de Errores

Soluciones a problemas comunes en Interactive Git Versioneer.

| Síntoma | Causa Raíz | Solución Técnica |
| :--- | :--- | :--- |
| `Error: Not a valid Git repository` | Directorio actual no es repo Git | Ejecutar `igv` desde directorio con `.git/` |
| `API key not configured` | Falta `OPENAI.key` en config | `igv config set OPENAI.key "<tu_api_key>"` |
| `Base URL not configured` | Falta `OPENAI.baseURL` en config | `igv config set OPENAI.baseURL "<url_proveedor>"` — ver [`configuracion_ia.md`](../referencia/configuracion_ia.md) |
| `GitHub CLI is not installed` | Falta `gh` en PATH | Instalar desde https://cli.github.com/ |
| `Not authenticated` | `gh` sin autenticación | Ejecutar `gh auth login` |
| `Error pushing tag` | Permisos o conectividad | Verificar `git remote -v` y permisos en repo |
| No se muestran commits | HEAD coincide con último tag | Crear nuevos commits antes de etiquetar |
| `Invalid or unconfigured API Key` | API key inválida o expirada | Verificar key en el panel del proveedor: Groq (`console.groq.com/keys`), OpenRouter (`openrouter.ai/keys`) |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-25 |
