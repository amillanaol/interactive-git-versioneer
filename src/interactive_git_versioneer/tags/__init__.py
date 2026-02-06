"""
Módulo de gestión de tags para interactive-git-versioneer.

Re-exporta las funciones de los módulos de tags para mantener compatibilidad.

Estructura de módulos:
- actions.py: Acciones sobre tags (crear, eliminar, sincronizar)
- ai.py: Integración con IA para generación de mensajes
- menus.py: Menús interactivos
- tagger.py: Módulo principal del tagger
- views.py: Funciones de visualización
"""

# Re-exportar modelos desde core
# Re-exportar operaciones Git desde core
from ..core.git_ops import (
    get_commit_diff,
    get_git_repo,
    get_last_tag,
    get_last_version_number,
    get_next_version,
    get_untagged_commits,
    parse_version,
)
from ..core.models import Commit

# Re-exportar acciones
from .actions import (
    apply_tags,
    change_last_tag,
    clean_all_tags,
    push_tags_to_remote,
    sync_tags_from_remote,
)

# Re-exportar funciones de IA
from .ai import (
    auto_generate_all_with_ai,
    generate_ai_message,
)

# Re-exportar menús
from .menus import (
    run_commits_submenu,
    run_tags_menu,
    show_commit_submenu,
)

# Re-exportar tagger
from .tagger import (
    run_auto_tagger,
    run_interactive_tagger,
)

# Re-exportar vistas
from .views import (
    paginate_items,
    select_commit_from_list,
    show_commit_details,
    show_commit_list,
    show_local_tags,
    show_remote_tags,
    show_tag_preview,
)

__all__ = [
    # Modelos
    "Commit",
    # Operaciones Git
    "get_git_repo",
    "get_last_tag",
    "get_untagged_commits",
    "get_commit_diff",
    "parse_version",
    "get_last_version_number",
    "get_next_version",
    # Vistas
    "show_commit_details",
    "show_commit_list",
    "select_commit_from_list",
    "show_tag_preview",
    "paginate_items",
    "show_local_tags",
    "show_remote_tags",
    # Acciones
    "apply_tags",
    "change_last_tag",
    "clean_all_tags",
    "push_tags_to_remote",
    "sync_tags_from_remote",
    # IA
    "generate_ai_message",
    "auto_generate_all_with_ai",
    # Menús
    "show_commit_submenu",
    "run_commits_submenu",
    "run_tags_menu",
    # Tagger
    "run_interactive_tagger",
    "run_auto_tagger",
]
