# Resolución de Errores

Soluciones a problemas comunes en Interactive Git Versioneer.

| Síntoma | Causa Raíz | Solución Técnica |
| :--- | :--- | :--- |
| `Error: Not a valid Git repository` | Directorio actual no es repo Git | Ejecutar `igv` desde directorio con `.git/` |
| `API key not configured` | Falta configuración OPENAI.key | `igv config set OPENAI.key "gsk_..."` |
| `Base URL not configured` | Falta OPENAI.baseURL | `igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"` |
| `GitHub CLI is not installed` | Falta `gh` en PATH | Instalar desde https://cli.github.com/ |
| `Not authenticated` | `gh` sin autenticación | Ejecutar `gh auth login` |
| `Error pushing tag` | Permisos o conectividad | Verificar `git remote -v` y permisos en repo |
| No se muestran commits | HEAD coincide con último tag | Crear nuevos commits antes de etiquetar |
| `Invalid or unconfigured API Key` | API key inválida o expirada | Verificar en https://console.groq.com/keys |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
