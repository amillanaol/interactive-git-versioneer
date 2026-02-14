| Necesidad | Ubicación |
| :--- | :--- |
| Generar documentación API automática | `mkdocstrings` |
| Ver docstrings de módulos | `src/interactive_git_versioneer/` |
| Documentar función específica | `:::` en archivo .md |

## Uso de mkdocstrings

La documentación API se genera automáticamente desde los docstrings del código fuente.

| Sintaxis | Resultado |
| :--- | :--- |
| `::: interactive_git_versioneer` | Documenta todo el paquete |
| `::: interactive_git_versioneer.core.git_ops` | Documenta módulo específico |
| `::: interactive_git_versioneer.main` | Documenta módulo principal |

## Ejemplo

```markdown
::: interactive_git_versioneer.core.git_ops
```

Genera documentación de: `get_git_repo()`, `parse_version()`, `get_last_tag()`, `get_next_version()`, `get_untagged_commits()`, `get_commit_diff()`.

## Módulos Documentables

| Módulo | Archivo |
| :--- | :--- |
| Core Git Ops | `src/interactive_git_versioneer/core/git_ops.py` |
| Core AI | `src/interactive_git_versioneer/core/ai.py` |
| Core Models | `src/interactive_git_versioneer/core/models.py` |
| Config | `src/interactive_git_versioneer/config/config.py` |
| Tags Actions | `src/interactive_git_versioneer/tags/actions.py` |
| Tags AI | `src/interactive_git_versioneer/tags/ai.py` |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
