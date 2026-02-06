# Core: AI Helpers

Descripción: utilidades para integrar con APIs de IA (OpenAI/Groq). Contiene funciones
para crear el cliente y generar mensajes/tipos de versión.

Funciones clave:

- `get_openai_client()` — Inicializa y devuelve el cliente configurado.
- `generate_tag_message(commit_message, commit_diff, version_type, ...)` — Genera un mensaje de tag.
- `determine_version_type(commit_message, commit_diff)` — Clasifica (major/minor/patch) y devuelve una razón.

Ejemplo de uso:

```python
from interactive_git_versioneer.core.ai import generate_tag_message, determine_version_type

vtype, reason = determine_version_type("Add feature X", "diff...")
msg = generate_tag_message("Add feature X", "diff...", vtype)
print(vtype, reason)
print(msg)
```

Notas:
- Requiere configuración `OPENAI.key` y `OPENAI.baseURL` en la configuración del proyecto.
