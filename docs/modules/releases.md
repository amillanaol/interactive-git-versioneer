# Releases: Gestión de releases y changelogs

Descripción: herramientas para integrar con releases remotos (p. ej. GitHub) y generar changelogs.

Funciones y flujos principales:

- `run_releases_menu(repo)` — Menú interactivo para releases.
- `run_changelog_submenu(repo)` — Submenú para generación/edición/guardado de changelogs.
- `action_generate_all_changelogs_with_ai(repo, rebuild=False)` — Regenera changelogs usando IA.

Ejemplo de uso (interactivo):

```python
from interactive_git_versioneer.tags.tagger import run_interactive_tagger
run_interactive_tagger()
```

Consejo: Usa `mkdocstrings` API para ver firma completa y ejemplos de cada función.
