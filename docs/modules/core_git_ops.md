# Core: Git Operations

Descripción: funciones de bajo nivel para interactuar con repositorios Git (envolviendo GitPython).

Funciones clave:

- `get_git_repo()` — Obtiene el `Repo` actual (lanza SystemExit si no es repo).
- `parse_version(tag)` — Parsea una etiqueta en `(major, minor, patch)`.
- `get_last_tag(repo)` — Devuelve el último tag disponible.
- `get_untagged_commits(repo)` — Lista commits posteriores al último tag.
- `get_commit_diff(repo, commit_hash)` — Obtiene el diff de un commit.

Ejemplo de uso:

```python
from interactive_git_versioneer.core.git_ops import get_git_repo, get_untagged_commits

repo = get_git_repo()
commits = get_untagged_commits(repo)
for c in commits:
    print(c.hash, c.message)
```

Consulta la sección **API** para detalles generados desde docstrings.
