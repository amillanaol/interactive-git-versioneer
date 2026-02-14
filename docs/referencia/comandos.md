# Comandos CLI

Referencia completa de comandos disponibles en `igv`.

## `igv [tag]`

Ejecuta el menú interactivo principal o subcomando de etiquetado.

| Flag | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `--dry-run` | Simula operaciones sin ejecutar | `igv tag --dry-run` |
| `--push` | Push automático de tags al remoto | `igv tag --push` |
| `--auto` | Modo automático CI/CD sin interacción | `igv tag --auto --type patch` |
| `--type` | Tipo de versión (major/minor/patch/auto) | `igv tag --auto --type minor` |

## `igv config <subcomando>`

Gestiona configuración en `~/.igv/config.json`.

| Subcomando | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `set <key> <value>` | Establece valor | `igv config set OPENAI.key "gsk_..."` |
| `get <key>` | Obtiene valor | `igv config get OPENAI.model` |
| `list` | Lista toda la configuración | `igv config list` |

### Claves de configuración

| Clave | Descripción |
| :--- | :--- |
| `OPENAI.key` | API key de Groq/OpenAI |
| `OPENAI.baseURL` | URL base (ej: `https://api.groq.com/openai/v1`) |
| `OPENAI.model` | Modelo (ej: `llama-3.3-70b-versatile`) |

## `igv clean-tags`

Elimina todos los tags locales y remotos. Operación destructiva irreversible.

| Flag | Descripción |
| :--- | :--- |
| `--local-only` | Solo elimina tags locales |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
