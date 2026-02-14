| Necesidad | Ubicación |
| :--- | :--- |
| Ejecutar menú interactivo | `igv` o `igv tag` |
| Configurar API de IA | `igv config set OPENAI.key <key>` |
| Etiquetado automático CI/CD | `igv tag --auto --push` |
| Simular cambios sin aplicar | `igv tag --dry-run` |
| Limpiar todos los tags | `igv clean-tags` |
| Ver configuración actual | `igv config list` |
| Punto de entrada CLI | `src/interactive_git_versioneer/main.py` |
| Configuración persistente | `~/.igv/config.json` |

## Instalación

| Método | Comando | Requisitos |
| :--- | :--- | :--- |
| PyPI (recomendado) | `pip install interactive-git-versioneer` | Python >= 3.7 |
| Desde Git | `pip install git+https://github.com/amillanaol/interactive-git-versioneer.git` | Git |
| Desarrollo | `git clone` + `pip install -e .` | Python >= 3.7, Git |

**Dependencias obligatorias:** `GitPython>=3.1.0`, `openai>=1.0.0`  
**Dependencias opcionales:** `gh` (GitHub CLI) para funciones de releases.

## Comandos CLI

### `igv [tag]`

Ejecuta el menú interactivo principal o subcomando de etiquetado.

| Flag | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `--dry-run` | Simula operaciones sin ejecutar | `igv tag --dry-run` |
| `--push` | Push automático de tags al remoto | `igv tag --push` |
| `--auto` | Modo automático CI/CD sin interacción | `igv tag --auto --type patch` |
| `--type` | Tipo de versión (major/minor/patch/auto) | `igv tag --auto --type minor` |

### `igv config <subcomando>`

Gestiona configuración en `~/.igv/config.json`.

| Subcomando | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `set <key> <value>` | Establece valor | `igv config set OPENAI.key "gsk_..."` |
| `get <key>` | Obtiene valor | `igv config get OPENAI.model` |
| `list` | Lista toda la configuración | `igv config list` |

**Claves de configuración soportadas:**
- `OPENAI.key` - API key de Groq/OpenAI
- `OPENAI.baseURL` - URL base (ej: `https://api.groq.com/openai/v1`)
- `OPENAI.model` - Modelo (ej: `llama-3.3-70b-versatile`)

### `igv clean-tags`

Elimina todos los tags locales y remotos. Operación destructiva irreversible.

| Flag | Descripción |
| :--- | :--- |
| `--local-only` | Solo elimina tags locales |

## Estructura de Módulos

| Módulo | Archivo Principal | Responsabilidad |
| :--- | :--- | :--- |
| **Core** | `src/interactive_git_versioneer/core/` | Operaciones base |
| Git Operations | `core/git_ops.py` | Interacción con repositorio Git |
| Version Operations | `core/version_ops.py` | Manejo de versiones SemVer |
| AI Integration | `core/ai.py` | Generación de mensajes con IA |
| Models | `core/models.py` | Definición de datos (Commit) |
| UI | `core/ui.py` | Utilidades de interfaz |
| Logger | `core/logger.py` | Sistema de logging |
| **Tags** | `src/interactive_git_versioneer/tags/` | Gestión de etiquetas |
| Tagger | `tags/tagger.py` | Lógica principal de etiquetado |
| Actions | `tags/actions.py` | Acciones sobre tags (crear, eliminar) |
| AI | `tags/ai.py` | Generación automática con IA |
| Menus | `tags/menus.py` | Menús interactivos |
| Views | `tags/views.py` | Visualización de datos |
| **Releases** | `src/interactive_git_versioneer/releases/` | Gestión de releases GitHub |
| GitHub Releases | `releases/gh_releases.py` | CRUD de releases via `gh` CLI |
| Changelog Gen | `releases/changelog_gen.py` | Generación de changelogs |
| Changelog Actions | `releases/changelog_actions.py` | Acciones sobre changelogs |
| Auth | `releases/gh_auth.py` | Autenticación GitHub CLI |
| **Config** | `src/interactive_git_versioneer/config/` | Configuración del sistema |
| Config | `config/config.py` | Lectura/escritura de config.json |
| Menu | `config/menu.py` | Menú de configuración |

## Flujos de Trabajo por Rol

### Desarrollador

| Tarea | Comando | Ubicación Código |
| :--- | :--- | :--- |
| Etiquetar commits pendientes | `igv` → "1. Gestionar Commits" | `tags/menus.py:run_commits_submenu()` |
| Ver diff de commit | Menú commits → seleccionar commit | `core/git_ops.py:get_commit_diff()` |
| Aplicar tags generados | Menú commits → "Aplicar tags" | `tags/actions.py:apply_tags()` |
| Generar mensaje con IA | Menú commits → "Auto-generar con IA" | `tags/ai.py:auto_generate_all_with_ai()` |
| Actualizar versión pyproject.toml | Menú tags → "Actualizar versión proyecto" | `core/version_ops.py:action_update_project_version()` |

### Operaciones (CI/CD)

| Tarea | Comando | Variable Entorno |
| :--- | :--- | :--- |
| Etiquetado automático | `igv tag --auto --push --type patch` | `OPENAI_KEY`, `GITHUB_TOKEN` |
| Simulación dry-run | `igv tag --auto --dry-run` | - |
| Crear release GitHub | Requiere `gh auth login` previo | `GH_TOKEN` |
| Generar changelog | Menú changelogs → "Continuar automático con IA" | `OPENAI_KEY` |

### Usuario Final

| Acción | Entrada | Resultado |
| :--- | :--- | :--- |
| Navegar menú | `igv` | Menú interactivo con opciones numeradas |
| Volver atrás | `Supr`, `Esc`, `-back-` | Nivel anterior del menú |
| Salir | `q`, `-exit-` | Termina la aplicación |
| Seleccionar opción | Número + `Enter` | Ejecuta acción correspondiente |

## Resolución de Errores

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

## Arquitectura de Datos

### Modelo Commit

| Atributo | Tipo | Descripción |
| :--- | :--- | :--- |
| `hash` | `str` | SHA del commit (40 chars) |
| `message` | `str` | Primera línea del mensaje |
| `author` | `str` | Nombre del autor |
| `date` | `str` | Fecha en formato `YYYY-MM-DD` |
| `version_type` | `str` | major/minor/patch/None |
| `custom_message` | `str` | Mensaje de tag personalizado |
| `processed` | `bool` | Estado de procesamiento |

Definición: `src/interactive_git_versioneer/core/models.py`

### Versionado Semántico

Formato: `v{major}.{minor}.{patch}`

| Incremento | Cambio | Ejemplo |
| :--- | :--- | :--- |
| major | Breaking changes | `v1.2.3` → `v2.0.0` |
| minor | Nuevas features | `v1.2.3` → `v1.3.0` |
| patch | Bug fixes | `v1.2.3` → `v1.2.4` |

Lógica: `src/interactive_git_versioneer/core/git_ops.py:get_next_version()`

## Configuración de IA

### Proveedores Soportados

| Proveedor | Base URL | Modelo por defecto |
| :--- | :--- | :--- |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` |

### Configuración Rápida

```bash
igv config set OPENAI.key "gsk_your_api_key"
igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"
igv config set OPENAI.model "llama-3.3-70b-versatile"
```

Implementación: `src/interactive_git_versioneer/core/ai.py:get_openai_client()`

## Logging

| Aspecto | Detalle |
| :--- | :--- |
| Ubicación | `~/.igv_logs/igv_debug_YYYYMMDD_HHMMSS.log` |
| Activación | Automática en cada ejecución |
| Contenido | Entradas/salidas de funciones, diálogos, selecciones de menú |
| Implementación | `src/interactive_git_versioneer/core/logger.py` |

## Referencias Cruzadas

- Configuración: [src/interactive_git_versioneer/config/config.py](src/interactive_git_versioneer/config/config.py)
- Operaciones Git: [src/interactive_git_versioneer/core/git_ops.py](src/interactive_git_versioneer/core/git_ops.py)
- Integración IA: [src/interactive_git_versioneer/core/ai.py](src/interactive_git_versioneer/core/ai.py)
- Acciones de tags: [src/interactive_git_versioneer/tags/actions.py](src/interactive_git_versioneer/tags/actions.py)
- Releases GitHub: [src/interactive_git_versioneer/releases/gh_releases.py](src/interactive_git_versioneer/releases/gh_releases.py)
- Changelogs: [src/interactive_git_versioneer/releases/changelog_gen.py](src/interactive_git_versioneer/releases/changelog_gen.py)

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
