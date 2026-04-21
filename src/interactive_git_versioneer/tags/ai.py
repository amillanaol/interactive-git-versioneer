"""
Integración con IA para interactive-git-versioneer.

Contiene funciones para generar mensajes y determinar tipos de versión usando IA.
"""

from typing import List, Optional

import git

from ..config import get_config_value
from ..core.git_ops import get_commit_diff, get_next_version, parse_version
from ..core.models import Commit
from ..core.ui import Colors, clear_screen, print_header, print_info, wait_for_enter


def _generate_with_provider(
    api_key: str,
    base_url: str,
    model: str,
    commit_message: str,
    commit_diff: str,
    version_type: str,
) -> Optional[str]:
    """Intenta generar mensaje con un proveedor específico."""
    from ..core.ai import OpenAiCompatibleAdapter

    try:
        adapter = OpenAiCompatibleAdapter(
            api_key=api_key, base_url=base_url, model=model
        )
        return adapter.generate_tag_message(
            commit_message=commit_message,
            commit_diff=commit_diff,
            version_type=version_type,
        )
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return None


def _editar_tag_manual(repo, commit, current_message) -> str:
    """Edita un tag manualmente cuando IA no está disponible."""
    from ..core.git_ops import get_next_version

    current_type = commit.version_type or "patch"
    current_version = getattr(commit, "custom_version", None) or get_next_version(
        repo, current_type
    )

    clear_screen()
    print_header("EDITAR TAG MANUAL")
    print()

    print(
        f"{Colors.WHITE}Tipo actual: {Colors.CYAN}{current_type.upper()}{Colors.RESET}"
    )
    print(
        f"{Colors.WHITE}Etiqueta actual: {Colors.CYAN}{current_version}{Colors.RESET}"
    )
    print()

    custom_version_input = input(
        f"{Colors.WHITE}Nueva versión (Enter para mantener {current_version}): {Colors.RESET}"
    ).strip()
    if custom_version_input:
        if not custom_version_input.startswith("v"):
            custom_version_input = "v" + custom_version_input
        commit.custom_version = custom_version_input
        current_version = custom_version_input
        print(f"{Colors.GREEN}Versión cambiada a: {current_version}{Colors.RESET}")

    print()
    print(f"{Colors.WHITE}Opciones tipo: [1] MAJOR  [2] MINOR  [3] PATCH{Colors.RESET}")
    type_choice = input(
        f"{Colors.WHITE}Nuevo tipo (Enter para mantener {current_type}): {Colors.RESET}"
    ).strip()
    if type_choice == "1":
        commit.version_type = "major"
    elif type_choice == "2":
        commit.version_type = "minor"
    elif type_choice == "3":
        commit.version_type = "patch"

    print()
    print(f"{Colors.WHITE}Mensaje actual:{Colors.RESET}")
    print(f"{Colors.CYAN}{current_message}{Colors.RESET}")
    new_message = input(
        f"{Colors.WHITE}Nuevo mensaje (Enter para mantener): {Colors.RESET}"
    ).strip()
    if new_message:
        current_message = new_message

    print(f"{Colors.GREEN}Tag actualizado:{Colors.RESET}")
    print(f"  Tipo: {commit.version_type.upper()}")
    print(
        f"  Versión: {getattr(commit, 'custom_version', None) or get_next_version(repo, commit.version_type)}"
    )
    print(f"  Mensaje: {current_message}")

    wait_for_enter()
    return current_message


def generate_ai_message(repo: git.Repo, commit: Commit) -> Optional[str]:
    """Genera un mensaje usando IA para un commit.

    Intenta primero con el proveedor configurado, y si falla por rate limit,
    intenta con Ollama si está disponible.

    Args:
        repo: Repositorio Git
        commit: Commit para el cual generar mensaje

    Returns:
        str o None: Mensaje generado o None si hay error
    """
    from ..config import get_config_value
    from ..core.ai import _is_local_provider, generate_tag_message

    api_key = get_config_value("OPENAI.key")
    base_url = get_config_value("OPENAI.baseURL")
    model = get_config_value("OPENAI.model") or "llama3.2"

    if not api_key and not _is_local_provider(base_url or ""):
        print(f"{Colors.RED}Error: API key no configurada.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Configúrala con: igv config set OPENAI.key <tu-api-key>{Colors.RESET}"
        )
        return None

    if not base_url:
        print(f"{Colors.RED}Error: Base URL no configurada.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Configúrala con: igv config set OPENAI.baseURL <url>{Colors.RESET}"
        )
        return None

    version_type = commit.version_type or "patch"

    print(f"{Colors.CYAN}Obteniendo diff del commit...{Colors.RESET}")
    diff = get_commit_diff(repo, commit.hash)

    print(f"{Colors.CYAN}Generando mensaje con IA...{Colors.RESET}")

    current_api_key = api_key
    if _is_local_provider(base_url):
        current_api_key = "ollama"

    message = _generate_with_provider(
        current_api_key, base_url, model, commit.message, diff, version_type
    )

    if message:
        return message

    if not _is_local_provider(base_url):
        ollama_url = "http://localhost:11434/v1"
        ollama_model = "llama3.2"
        print(
            f"{Colors.YELLOW}Proveedor principal no disponible. Intentando con Ollama...{Colors.RESET}"
        )

        message = _generate_with_provider(
            "ollama", ollama_url, ollama_model, commit.message, diff, version_type
        )
        if message:
            print(f"{Colors.GREEN}✓ Mensaje generado con Ollama{Colors.RESET}")
            return message

    return None


def auto_generate_all_with_ai(repo: git.Repo, commits: List[Commit]) -> None:
    """Genera automáticamente mensajes con IA para todos los commits.

    Args:
        repo: Repositorio Git
        commits: Lista de commits a procesar
    """
    from ..config import get_config_value
    from ..core.ai import determine_version_type

    clear_screen()
    print_header("GENERAR TAGS")

    if not get_config_value("OPENAI.key") or not get_config_value("OPENAI.baseURL"):
        print(f"{Colors.RED}Error: Configuración de IA incompleta.{Colors.RESET}")
        print(f"{Colors.YELLOW}Configura con:{Colors.RESET}")
        print(
            f"  python -m interactive_git_versioneer.main config set OPENAI.key <tu-api-key>"
        )
        print(
            f"  python -m interactive_git_versioneer.main config set OPENAI.baseURL <url>"
        )
        return

    print()
    print(f"{Colors.WHITE}Seleccione el modo de asignación de versión:{Colors.RESET}")
    print(f"{Colors.WHITE}1. Usar mensaje del commit (semiautomático){Colors.RESET}")
    print(f"{Colors.WHITE}2. Elegir manualmente uno a uno (sin IA){Colors.RESET}")
    print(
        f"{Colors.WHITE}3. Generar con IA uno a uno con previsualización{Colors.RESET}"
    )
    print(f"{Colors.WHITE}4. Dejar que la IA los genere (automático){Colors.RESET}")
    print()

    type_choice = input(
        f"{Colors.WHITE}Seleccione opción (1-4): {Colors.RESET}"
    ).strip()

    if type_choice not in ("1", "2", "3", "4"):
        print(f"{Colors.RED}Opción inválida. Operación cancelada.{Colors.RESET}")
        return

    if type_choice == "1":
        sorted_commits = sorted(commits, key=lambda c: c.datetime)
        generate_tags_with_commit_message(repo, sorted_commits)
        return
    elif type_choice == "2":
        sorted_commits = sorted(commits, key=lambda c: c.datetime)
        generate_tags_manual(repo, sorted_commits)
        return
    elif type_choice == "3":
        sorted_commits = sorted(commits, key=lambda c: c.datetime)
        generate_ai_tags_one_by_one(repo, sorted_commits)
        return

    ai_decides = type_choice == "4"

    print()
    if ai_decides:
        print(
            f"{Colors.CYAN}La IA determinará el tipo de versión para cada commit automáticamente{Colors.RESET}"
        )
    else:
        print(
            f"{Colors.CYAN}Podrás elegir el tipo de versión para cada commit{Colors.RESET}"
        )
    print(f"{Colors.CYAN}Procesando {len(commits)} commits...{Colors.RESET}")
    print()

    success_count = 0
    error_count = 0
    skipped_count = 0

    for i, commit in enumerate(commits, 1):
        print(
            f"{Colors.WHITE}[{i}/{len(commits)}] {commit.hash[:7]} - {commit.message[:50]}...{Colors.RESET}"
        )

        if ai_decides:
            print(f"  {Colors.CYAN}Analizando tipo de versión...{Colors.RESET}")
            diff = get_commit_diff(repo, commit.hash)
            try:
                version_type, reason = determine_version_type(commit.message, diff)
                commit.version_type = version_type
                print(
                    f"  {Colors.GREEN}→ {version_type.upper()}: {reason}{Colors.RESET}"
                )
            except Exception as e:
                error_str = str(e).lower()
                if (
                    "401" in error_str
                    or "invalid_api_key" in error_str
                    or "invalid api key" in error_str
                ):
                    print(
                        f"  {Colors.RED}✗ API Key inválida. Ejecuta: igv config → Configure AI{Colors.RESET}"
                    )
                else:
                    print(
                        f"  {Colors.RED}✗ Error al determinar tipo: {e}{Colors.RESET}"
                    )
                commit.version_type = "patch"
                print(f"  {Colors.YELLOW}→ Usando PATCH por defecto{Colors.RESET}")
        elif interactive_mode:
            # Modo interactivo: permitir elegir para cada commit
            print(
                f"  {Colors.WHITE}Opciones: [1] MAJOR  [2] MINOR  [3] PATCH  [s] saltar{Colors.RESET}"
            )
            try:
                choice = (
                    input(f"  {Colors.WHITE}Seleccione: {Colors.RESET}").strip().lower()
                )
            except KeyboardInterrupt:
                print()
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                return

            if choice == "s":
                print(f"  {Colors.YELLOW}→ Commit saltado{Colors.RESET}")
                skipped_count += 1
                print()
                continue
            elif choice == "1":
                commit.version_type = "major"
            elif choice == "2":
                commit.version_type = "minor"
            elif choice == "3":
                commit.version_type = "patch"
            else:
                print(
                    f"  {Colors.YELLOW}Opción no reconocida, usando PATCH{Colors.RESET}"
                )
                commit.version_type = "patch"

            print(
                f"  {Colors.GREEN}→ Tipo seleccionado: {commit.version_type.upper()}{Colors.RESET}"
            )

        ai_message = generate_ai_message(repo, commit)

        if ai_message:
            commit.custom_message = ai_message
            commit.processed = True
            success_count += 1
            print(f"  {Colors.GREEN}✓ Mensaje generado{Colors.RESET}")
        else:
            error_count += 1
            print(f"  {Colors.RED}✗ Error al generar mensaje{Colors.RESET}")

        print()

    print_header("RESUMEN DE GENERACIÓN")
    print(
        f"Commits procesados exitosamente: {Colors.GREEN}{success_count}{Colors.RESET}"
    )
    if skipped_count > 0:
        print(f"Commits saltados: {Colors.YELLOW}{skipped_count}{Colors.RESET}")
    if error_count > 0:
        print(f"Errores: {Colors.RED}{error_count}{Colors.RESET}")
    print()

    # Si hay commits procesados, aplicar los tags
    if success_count > 0:
        from ..core.ui import wait_for_enter
        from .actions import apply_tags

        processed_commits = [c for c in commits if c.processed and c.version_type]
        if processed_commits:
            print(
                f"{Colors.YELLOW}¿Desea aplicar las {len(processed_commits)} etiquetas generadas?{Colors.RESET}"
            )
            try:
                apply_confirm = (
                    input(f"{Colors.WHITE}(s/n): {Colors.RESET}").strip().lower()
                )
                if apply_confirm == "s":
                    print()
                    success = apply_tags(
                        repo, processed_commits, dry_run=False, push=False
                    )
                    if success:
                        print()
                        print(
                            f"{Colors.GREEN}✓ Etiquetas aplicadas correctamente{Colors.RESET}"
                        )
                        print()

                        # Preguntar si desea subir al remoto
                        print(
                            f"{Colors.YELLOW}¿Desea subir las etiquetas al repositorio remoto?{Colors.RESET}"
                        )
                        push_confirm = (
                            input(f"{Colors.WHITE}(s/n): {Colors.RESET}")
                            .strip()
                            .lower()
                        )
                        if push_confirm == "s":
                            print()
                            print(
                                f"{Colors.CYAN}Subiendo tags al remoto...{Colors.RESET}"
                            )
                            try:
                                repo.remotes.origin.push(tags=True)
                                print(
                                    f"{Colors.GREEN}✓ Tags subidos exitosamente{Colors.RESET}"
                                )
                            except Exception as e:
                                print(
                                    f"{Colors.RED}✗ Error al subir tags: {e}{Colors.RESET}"
                                )
            except KeyboardInterrupt:
                print()
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")


def generate_tags_manual(repo: git.Repo, commits: List[Commit]) -> None:
    """Genera tags manualmente sin IA, usando mensaje del commit."""
    from ..core.git_ops import get_last_tag, parse_version

    commits = sorted(commits, key=lambda c: c.datetime)

    print()
    print(
        f"{Colors.CYAN}Procesando {len(commits)} commits manualmente...{Colors.RESET}"
    )
    print()

    last_tag = get_last_tag(repo)
    major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

    success_count = 0
    skipped_count = 0

    for i, commit in enumerate(commits, 1):
        clear_screen()
        print_header(f"GENERAR TAG MANUAL [{i}/{len(commits)}]")

        print_info("Commit:", commit.hash[:7], Colors.CYAN)
        print_info("Mensaje:", commit.message, Colors.WHITE)
        print()

        print(
            f"{Colors.WHITE}Opciones tipo: [1] MAJOR  [2] MINOR  [3] PATCH  [s] saltar{Colors.RESET}"
        )
        try:
            choice = input(f"{Colors.WHITE}Seleccione: {Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")
            return

        if choice == "s":
            print(f"  {Colors.YELLOW}→ Commit saltado{Colors.RESET}")
            skipped_count += 1
            print()
            wait_for_enter()
            continue
        elif choice == "1":
            commit.version_type = "major"
        elif choice == "2":
            commit.version_type = "minor"
        elif choice == "3":
            commit.version_type = "patch"
        else:
            commit.version_type = "patch"

        commit.custom_message = commit.message.strip()
        commit.processed = True
        success_count += 1

        if commit.version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif commit.version_type == "minor":
            minor += 1
            patch = 0
        elif commit.version_type == "patch":
            patch += 1
        next_ver = f"v{major}.{minor}.{patch}"
        commit.custom_version = next_ver
        print(
            f"  {Colors.GREEN}→ Tipo: {commit.version_type.upper()} | Tag: {next_ver}{Colors.RESET}"
        )
        print()
        wait_for_enter()

    clear_screen()
    print_header("RESUMEN")
    print(f"Procesados: {Colors.GREEN}{success_count}{Colors.RESET}")
    if skipped_count > 0:
        print(f"Saltados: {Colors.YELLOW}{skipped_count}{Colors.RESET}")

    # Mostrar detalle de commits procesados
    if success_count > 0:
        print()
        print(f"{Colors.WHITE}Detalle de versiones:{Colors.RESET}")
        from ..core.git_ops import get_last_tag, parse_version

        last_tag = get_last_tag(repo)
        major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

        for commit in commits:
            if not commit.processed or not commit.version_type:
                continue
            if getattr(commit, "custom_version", None):
                version = commit.custom_version
                parsed = parse_version(version)
                if parsed:
                    major, minor, patch = parsed
            else:
                if commit.version_type == "major":
                    major += 1
                    minor = 0
                    patch = 0
                elif commit.version_type == "minor":
                    minor += 1
                    patch = 0
                elif commit.version_type == "patch":
                    patch += 1
                version = f"v{major}.{minor}.{patch}"
            print(
                f"  {Colors.CYAN}{version}{Colors.RESET} ← {Colors.WHITE}{commit.hash[:7]}{Colors.RESET}"
            )

    print()

    if success_count > 0:
        from .actions import apply_tags

        processed = [c for c in commits if c.processed and c.version_type]
        print(f"{Colors.YELLOW}¿Aplicar {len(processed)} etiquetas?{Colors.RESET}")
        try:
            if input(f"{Colors.WHITE}(s/n): {Colors.RESET}").strip().lower() == "s":
                apply_tags(repo, processed, dry_run=False, push=False)
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")


def generate_tags_with_commit_message(repo: git.Repo, commits: List[Commit]) -> None:
    """Genera tags usando el mensaje del commit automáticamente."""
    from ..core.git_ops import get_last_tag, parse_version

    commits = sorted(commits, key=lambda c: c.datetime)

    print()
    print(f"{Colors.CYAN}Procesando {len(commits)} commits...{Colors.RESET}")
    print()

    last_tag = get_last_tag(repo)
    major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

    success_count = 0
    skipped_count = 0

    for i, commit in enumerate(commits, 1):
        clear_screen()
        print_header(f"GENERAR TAG [{i}/{len(commits)}]")

        print_info("Commit:", commit.hash[:7], Colors.CYAN)
        print_info("Mensaje:", commit.message, Colors.WHITE)
        print()

        print(
            f"{Colors.WHITE}Opciones: [1] MAJOR  [2] MINOR  [3] PATCH  [s] saltar{Colors.RESET}"
        )
        try:
            choice = input(f"{Colors.WHITE}Seleccione: {Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return

        if choice == "s":
            print(f"  {Colors.YELLOW}→ Commit saltado{Colors.RESET}")
            skipped_count += 1
            print()
            wait_for_enter()
            continue
        elif choice == "1":
            commit.version_type = "major"
        elif choice == "2":
            commit.version_type = "minor"
        elif choice == "3":
            commit.version_type = "patch"
        else:
            commit.version_type = "patch"

        commit.custom_message = commit.message.strip()
        commit.processed = True
        success_count += 1

        if commit.version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif commit.version_type == "minor":
            minor += 1
            patch = 0
        elif commit.version_type == "patch":
            patch += 1
        next_ver = f"v{major}.{minor}.{patch}"
        commit.custom_version = next_ver
        print(
            f"  {Colors.GREEN}→ Tipo: {commit.version_type.upper()} | Tag: {next_ver}{Colors.RESET}"
        )
        print()

        edit_version = input(
            f"{Colors.WHITE}¿Cambiar versión? (Enter para mantener/{next_ver}): {Colors.RESET}"
        ).strip()
        if edit_version:
            if not edit_version.startswith("v"):
                edit_version = "v" + edit_version
            commit.custom_version = edit_version
            parsed = parse_version(edit_version)
            if parsed:
                major, minor, patch = parsed
            print(f"{Colors.GREEN}  → Versión cambiada a: {edit_version}{Colors.RESET}")

        print()
        wait_for_enter()

    clear_screen()
    print_header("RESUMEN")
    print(f"Procesados: {Colors.GREEN}{success_count}{Colors.RESET}")
    if skipped_count > 0:
        print(f"Saltados: {Colors.YELLOW}{skipped_count}{Colors.RESET}")

    # Mostrar detalle de commits procesados
    if success_count > 0:
        print()
        print(f"{Colors.WHITE}Detalle de versiones:{Colors.RESET}")
        from ..core.git_ops import get_last_tag, parse_version

        last_tag = get_last_tag(repo)
        major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

        for commit in commits:
            if not commit.processed or not commit.version_type:
                continue
            if getattr(commit, "custom_version", None):
                version = commit.custom_version
                parsed = parse_version(version)
                if parsed:
                    major, minor, patch = parsed
            else:
                if commit.version_type == "major":
                    major += 1
                    minor = 0
                    patch = 0
                elif commit.version_type == "minor":
                    minor += 1
                    patch = 0
                elif commit.version_type == "patch":
                    patch += 1
                version = f"v{major}.{minor}.{patch}"
            print(
                f"  {Colors.CYAN}{version}{Colors.RESET} ← {Colors.WHITE}{commit.hash[:7]}{Colors.RESET}"
            )

    print()

    if success_count > 0:
        from .actions import apply_tags

        processed = [c for c in commits if c.processed and c.version_type]
        print(f"{Colors.YELLOW}¿Aplicar {len(processed)} etiquetas?{Colors.RESET}")
        try:
            if input(f"{Colors.WHITE}(s/n): {Colors.RESET}").strip().lower() == "s":
                apply_tags(repo, processed, dry_run=False, push=False)
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")


def generate_ai_tags_one_by_one(repo: git.Repo, commits: List[Commit]) -> None:
    """Genera tags con IA uno a uno con previsualización detallada."""
    from ..core.ai import determine_version_type
    from ..core.git_ops import get_next_version

    if not get_config_value("OPENAI.key") or not get_config_value("OPENAI.baseURL"):
        print(f"{Colors.RED}Error: Configuración de IA incompleta.{Colors.RESET}")
        return

    commits = sorted(commits, key=lambda c: c.datetime)

    print()
    print(f"{Colors.WHITE}Seleccione el modo de asignación de versión:{Colors.RESET}")
    print(f"{Colors.WHITE}1. Elegir tipo uno a uno (interactivo){Colors.RESET}")
    print(f"{Colors.WHITE}2. Dejar que la IA decida (automático){Colors.RESET}")
    print()

    type_choice = input(
        f"{Colors.WHITE}Seleccione opción (1-2): {Colors.RESET}"
    ).strip()

    if type_choice not in ("1", "2"):
        print(f"{Colors.RED}Opción inválida.{Colors.RESET}")
        return

    ai_decides = type_choice == "2"
    interactive_mode = type_choice == "1"

    print()
    print(f"{Colors.CYAN}Procesando {len(commits)} commits...{Colors.RESET}")
    print()

    success_count = 0
    error_count = 0
    skipped_count = 0

    for i, commit in enumerate(commits, 1):
        clear_screen()
        print_header(f"GENERAR TAG CON IA [{i}/{len(commits)}]")

        print_info("Commit:", commit.hash[:7], Colors.CYAN)
        print_info("Mensaje:", commit.message, Colors.WHITE)
        print()

        if ai_decides:
            print(f"{Colors.CYAN}Analizando tipo de versión...{Colors.RESET}")
            diff = get_commit_diff(repo, commit.hash)
            try:
                version_type, reason = determine_version_type(commit.message, diff)
                commit.version_type = version_type
                print(
                    f"  {Colors.GREEN}→ {version_type.upper()}: {reason}{Colors.RESET}"
                )
            except Exception as e:
                commit.version_type = "patch"
                print(f"  {Colors.YELLOW}→ Usando PATCH por defecto{Colors.RESET}")
        elif interactive_mode:
            print(
                f"{Colors.WHITE}Opciones: [1] MAJOR  [2] MINOR  [3] PATCH  [s] saltar{Colors.RESET}"
            )
            try:
                choice = (
                    input(f"{Colors.WHITE}Seleccione: {Colors.RESET}").strip().lower()
                )
            except KeyboardInterrupt:
                print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")
                return

            if choice == "s":
                skipped_count += 1
                wait_for_enter()
                continue
            elif choice == "1":
                commit.version_type = "major"
            elif choice == "2":
                commit.version_type = "minor"
            elif choice == "3":
                commit.version_type = "patch"
            else:
                commit.version_type = "patch"
            print(f"  {Colors.GREEN}→ {commit.version_type.upper()}{Colors.RESET}")

        print()
        print(f"{Colors.CYAN}Generando mensaje con IA...{Colors.RESET}")
        ai_message = generate_ai_message(repo, commit)

        if not ai_message:
            print(f"{Colors.RED}No fue posible autogenerar con IA.{Colors.RESET}")
            print(
                f"{Colors.YELLOW}Usando mensaje del commit. Puede editarlo.{Colors.RESET}"
            )
            ai_message = commit.message.strip()
            commit.version_type = commit.version_type or "patch"
            commit.custom_message = ai_message
            commit.processed = True
            success_count += 1

            print()
            print_header("PREVISUALIZACIÓN DEL TAG")
            print()
            current_version = getattr(
                commit, "custom_version", None
            ) or get_next_version(repo, commit.version_type)
            print_info("Commit:", commit.hash[:7], Colors.CYAN)
            print_info("Etiqueta:", current_version, Colors.GREEN)
            print_info("Tipo:", commit.version_type.upper(), Colors.GREEN)
            print_info("Mensaje:", ai_message, Colors.CYAN)
            print()
            print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
            print()

            try:
                use_message = (
                    input(
                        f"{Colors.WHITE}¿Usar este mensaje? (s/n/e=editar): {Colors.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except KeyboardInterrupt:
                print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")
                return

            if use_message == "e":
                commit.custom_message = _editar_tag_manual(repo, commit, ai_message)
            elif use_message != "s":
                commit.custom_message = None
                commit.version_type = None
                commit.processed = False
                success_count -= 1

        if ai_message:
            commit.processed = True
            success_count += 1

            clear_screen()
            print_header("PREVISUALIZACIÓN DEL TAG")
            print()
            current_version = getattr(
                commit, "custom_version", None
            ) or get_next_version(repo, commit.version_type)
            print_info("Commit:", commit.hash[:7], Colors.CYAN)
            print_info("Etiqueta:", current_version, Colors.GREEN)
            print_info("Tipo:", commit.version_type.upper(), Colors.GREEN)
            print_info("Mensaje:", ai_message, Colors.CYAN)
            print()
            print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
            print()

            try:
                use_message = (
                    input(
                        f"{Colors.WHITE}¿Usar? (s/n/r=regenerar/e=editar/a=aplicar): {Colors.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except KeyboardInterrupt:
                print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")
                return

            if use_message == "r":
                ai_message = generate_ai_message(repo, commit)
                if ai_message:
                    commit.custom_message = ai_message
                wait_for_enter()
            elif use_message == "e":
                clear_screen()
                print_header("EDITAR TAG")
                print()

                current_type = commit.version_type or "patch"
                current_version = getattr(
                    commit, "custom_version", None
                ) or get_next_version(repo, current_type)

                print(
                    f"{Colors.WHITE}Tipo actual: {Colors.CYAN}{current_type.upper()}{Colors.RESET}"
                )
                print(
                    f"{Colors.WHITE}Etiqueta actual: {Colors.CYAN}{current_version}{Colors.RESET}"
                )
                print()

                custom_version_input = input(
                    f"{Colors.WHITE}Nueva versión (Enter para mantener {current_version}): {Colors.RESET}"
                ).strip()
                if custom_version_input:
                    if not custom_version_input.startswith("v"):
                        custom_version_input = "v" + custom_version_input
                    commit.custom_version = custom_version_input
                    current_version = custom_version_input
                    print(
                        f"{Colors.GREEN}Versión cambiada a: {current_version}{Colors.RESET}"
                    )

                print()
                print(
                    f"{Colors.WHITE}Opciones tipo: [1] MAJOR  [2] MINOR  [3] PATCH{Colors.RESET}"
                )
                type_choice = input(
                    f"{Colors.WHITE}Nuevo tipo (Enter para mantener {current_type}): {Colors.RESET}"
                ).strip()
                if type_choice == "1":
                    commit.version_type = "major"
                elif type_choice == "2":
                    commit.version_type = "minor"
                elif type_choice == "3":
                    commit.version_type = "patch"

                print()
                print(f"{Colors.WHITE}Mensaje actual:{Colors.RESET}")
                print(f"{Colors.CYAN}{ai_message}{Colors.RESET}")
                new_message = input(
                    f"{Colors.WHITE}Nuevo mensaje (Enter para mantener): {Colors.RESET}"
                ).strip()
                if new_message:
                    ai_message = new_message
                    commit.custom_message = ai_message

                print()
                custom_version = input(
                    f"{Colors.WHITE}Nueva versión (Enter para auto): {Colors.RESET}"
                ).strip()
                if custom_version:
                    if not custom_version.startswith("v"):
                        custom_version = "v" + custom_version
                    commit.custom_version = custom_version

                print(f"{Colors.GREEN}Tag actualizado:{Colors.RESET}")
                print(f"  Tipo: {commit.version_type.upper()}")
                print(
                    f"  Versión: {getattr(commit, 'custom_version', None) or get_next_version(repo, commit.version_type)}"
                )
                print(f"  Mensaje: {ai_message}")
                wait_for_enter()
            elif use_message == "a":
                from .actions import apply_tags

                commit.custom_message = ai_message
                commit.processed = True
                success_count += 1
                apply_tags(
                    repo, [commit], dry_run=False, push=False, skip_dirty_check=True
                )
                wait_for_enter()
            elif use_message != "s":
                commit.custom_message = None
                commit.version_type = None
                commit.processed = False
                success_count -= 1
        else:
            error_count += 1
            wait_for_enter()

    clear_screen()
    print_header("RESUMEN")
    print(f"Procesados: {Colors.GREEN}{success_count}{Colors.RESET}")
    if skipped_count > 0:
        print(f"Saltados: {Colors.YELLOW}{skipped_count}{Colors.RESET}")
    if error_count > 0:
        print(f"Errores: {Colors.RED}{error_count}{Colors.RESET}")

    # Mostrar detalle de commits procesados
    if success_count > 0:
        print()
        print(f"{Colors.WHITE}Detalle de versiones:{Colors.RESET}")
        from ..core.git_ops import get_next_version, get_last_tag
        from ..core.git_ops import parse_version

        last_tag = get_last_tag(repo)
        major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

        for commit in commits:
            if not commit.processed or not commit.version_type:
                continue
            if getattr(commit, "custom_version", None):
                version = commit.custom_version
                parsed = parse_version(version)
                if parsed:
                    major, minor, patch = parsed
            else:
                if commit.version_type == "major":
                    major += 1
                    minor = 0
                    patch = 0
                elif commit.version_type == "minor":
                    minor += 1
                    patch = 0
                elif commit.version_type == "patch":
                    patch += 1
                version = f"v{major}.{minor}.{patch}"
            print(
                f"  {Colors.CYAN}{version}{Colors.RESET} ← {Colors.WHITE}{commit.hash[:7]}{Colors.RESET}"
            )

    print()

    if success_count > 0:
        from .actions import apply_tags

        processed_commits = [c for c in commits if c.processed and c.version_type]
        if processed_commits:
            print(
                f"{Colors.YELLOW}¿Aplicar {len(processed_commits)} etiquetas?{Colors.RESET}"
            )
            try:
                if input(f"{Colors.WHITE}(s/n): {Colors.RESET}").strip().lower() == "s":
                    apply_tags(repo, processed_commits, dry_run=False, push=False)
            except KeyboardInterrupt:
                pass

    wait_for_enter()
