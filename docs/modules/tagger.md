# Tags: Tagger interactivo

Descripción: interfaz y utilidades para gestionar tags localmente y en remoto.

Funciones y comandos relevantes:

- `run_interactive_tagger(dry_run=False, push=False)` — Interfaz principal interactiva.
- `run_auto_tagger(dry_run=False, push=False, version_type="auto")` — Modo no interactivo (CI).
- `manage_tags_interactive(repo, dry_run=False, push=False)` — Submenú para modificar tags.

Ejemplo (modo automático):

```bash
igv tag --auto --push
```

Para más detalles de parámetros y retornos, revisa la referencia API.
