# Modelos de Datos

Estructuras de datos principales en Interactive Git Versioneer.

## Modelo Commit

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

## Versionado Semántico

Especificación: [SemVer](https://semver.org/lang/es/)

Formato: `v{major}.{minor}.{patch}`

| Incremento | Cambio | Ejemplo |
| :--- | :--- | :--- |
| major | Breaking changes | `v1.2.3` → `v2.0.0` |
| minor | Nuevas features | `v1.2.3` → `v1.3.0` |
| patch | Bug fixes | `v1.2.3` → `v1.2.4` |

Lógica: `src/interactive_git_versioneer/core/git_ops.py:get_next_version()`

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
