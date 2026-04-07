| Necesidad | Ubicación |
| :--- | :--- |
| Detectar commits con múltiples tags | `src/interactive_git_versioneer/tags/actions.py:clean_duplicate_tags()` |
| Ejecutar limpieza de tags duplicados | Menú Tags → Opción `d` |
| Eliminar tags localmente | `git tag -d <tag>` |
| Eliminar tags remotamente | `git push origin --delete <tag>` |
| Analizar tags duplicados | `clean_duplicate_tags(repo, include_remote=True)` |

## Funcionamiento

| Paso | Descripción | Implementación |
| :--- | :--- | :--- |
| 1 | Análisis de tags | `repo.tags` agrupados por commit SHA |
| 2 | Detección de duplicados | Commits con múltiples tags |
| 3 | Selección | Tag con versión semántica más alta vía `parse_version()` |
| 4 | Confirmación | Solicitud al usuario antes de eliminar |
| 5 | Eliminación local | `repo.delete_tag(tag_name)` |
| 6 | Eliminación remota | `git push --delete origin <tag>` |

## Acceso

Ejecutar `igv` → Opción `2. Tags` → Opción `d. Limpiar tags duplicados`.

## Criterio de Selección

Para cada commit con múltiples tags, se conserva el tag con la versión semántica más alta.

| Ejemplo de Entrada | Tag Conservado | Tags Eliminados |
| :--- | :--- | :--- |
| `v0.17.0`, `v0.20.0`, `v0.23.0`, `v0.26.0` | `v0.26.0` | `v0.17.0`, `v0.20.0`, `v0.23.0` |

## API

```python
from interactive_git_versioneer.tags import clean_duplicate_tags
from git import Repo

repo = Repo(".")
success = clean_duplicate_tags(repo, include_remote=True)
```

Parámetros: `repo` (Repo), `include_remote` (bool, default=True). Retorna: `bool`.

## Resolución de Errores

| Síntoma | Causa Raíz | Solución Técnica |
| :--- | :--- | :--- |
| No se pudo eliminar tag remoto | Falta permisos o tag protegido | Verificar permisos en GitHub Settings → Branches/Tags |
| Tag no encontrado | Tag ya eliminado o no sincronizado | Ejecutar `git fetch --tags` |
| Versión incorrecta seleccionada | Formato de tag no SemVer | Verificar formato `v{major}.{minor}.{patch}` |

## Precauciones

Operación destructiva. Elimina tags local y remotamente. Crear backup antes de ejecutar. Comunicar al equipo en entornos colaborativos.

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
