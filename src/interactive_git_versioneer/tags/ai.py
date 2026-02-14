"""
Integración con IA para interactive-git-versioneer.

Contiene funciones para generar mensajes y determinar tipos de versión usando IA.
"""

from typing import List, Optional

import git

from ..core.git_ops import get_commit_diff, get_next_version, parse_version
from ..core.models import Commit
from ..core.ui import Colors, clear_screen, print_header


def generate_ai_message(repo: git.Repo, commit: Commit) -> Optional[str]:
    """Genera un mensaje usando IA para un commit.

    Args:
        repo: Repositorio Git
        commit: Commit para el cual generar mensaje

    Returns:
        str o None: Mensaje generado o None si hay error
    """
    from ..config import get_config_value
    from ..core.ai import generate_tag_message

    if not get_config_value("OPENAI.key"):
        print(f"{Colors.RED}Error: API key no configurada.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Configúrala con: igv config set OPENAI.key <tu-api-key>{Colors.RESET}"
        )
        return None

    if not get_config_value("OPENAI.baseURL"):
        print(f"{Colors.RED}Error: Base URL no configurada.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Configúrala con: igv config set OPENAI.baseURL <url>{Colors.RESET}"
        )
        return None

    version_type = commit.version_type or "patch"

    print(f"{Colors.CYAN}Obteniendo diff del commit...{Colors.RESET}")
    diff = get_commit_diff(repo, commit.hash)

    print(f"{Colors.CYAN}Generando mensaje con IA...{Colors.RESET}")
    try:
        message = generate_tag_message(
            commit_message=commit.message, commit_diff=diff, version_type=version_type
        )
        return message
    except ImportError as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return None
    except Exception as e:
        error_str = str(e).lower()
        if (
            "401" in error_str
            or "invalid_api_key" in error_str
            or "invalid api key" in error_str
        ):
            print(
                f"{Colors.RED}Error: API Key inválida o no configurada.{Colors.RESET}"
            )
            print(f"{Colors.YELLOW}Configura tu API key con:{Colors.RESET}")
            print(f'  igv config set OPENAI.key "tu_api_key"')
            print(f'  igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"')
            print(f'  igv config set OPENAI.model "llama-3.3-70b-versatile"')
            print(
                f"{Colors.CYAN}Obtén tu API key en: https://console.groq.com/keys{Colors.RESET}"
            )
        else:
            print(f"{Colors.RED}Error al generar mensaje: {e}{Colors.RESET}")
        return None


def auto_generate_all_with_ai(
    repo: git.Repo, commits: List[Commit], skip_changelog_check: bool = False
) -> None:
    """Genera automáticamente mensajes con IA para todos los commits.

    Args:
        repo: Repositorio Git
        commits: Lista de commits a procesar
        skip_changelog_check: Si es True, omite la verificación de changelog desactualizado
    """
    from ..config import get_config_value
    from ..core.ai import determine_version_type
    from .actions import _get_changelog_versions

    clear_screen()
    print_header("AUTO-GENERAR TAGS CON IA")

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

    # Verificar changelog ANTES de usar la IA (solo si no se omite la verificación)
    if not skip_changelog_check:
        from ..core.git_ops import get_last_tag

        # Calculamos las versiones que se crearán para los commits pendientes (INCREMENTAL)
        changelog_versions = _get_changelog_versions(repo)
        pending_versions = []

        # Obtener la versión base (última versión del repo)
        last_tag = get_last_tag(repo)
        major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

        for commit in commits:
            # Asumimos patch como mínimo para calcular las próximas versiones
            patch += 1
            next_ver = f"v{major}.{minor}.{patch}"
            if next_ver not in pending_versions:
                pending_versions.append(next_ver)

        # Verificar si las versiones pendientes están en el changelog
        missing_in_changelog = [
            v for v in pending_versions if v not in changelog_versions
        ]

        if missing_in_changelog:
            print()
            print(
                f"{Colors.RED}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}"
            )
            print(
                f"{Colors.RED}║  ⚠️  ADVERTENCIA: CHANGELOG DESACTUALIZADO                   ║{Colors.RESET}"
            )
            print(
                f"{Colors.RED}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}"
            )
            print()
            print(
                f"{Colors.YELLOW}La próxima versión ({missing_in_changelog[0]}) no está registrada en CHANGELOG.md{Colors.RESET}"
            )
            print()
            print(
                f"{Colors.YELLOW}Se recomienda actualizar el changelog antes de crear nuevos tags.{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}Puede hacerlo desde: Gestionar Changelogs → Continuar changelog (con IA){Colors.RESET}"
            )
            print()

            try:
                confirm = (
                    input(
                        f"{Colors.WHITE}¿Desea continuar de todos modos? (s/n): {Colors.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except KeyboardInterrupt:
                print()
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                return

            if confirm != "s":
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                return

    print()
    print(f"{Colors.WHITE}Seleccione el modo de asignación de versión:{Colors.RESET}")
    print(f"{Colors.WHITE}1. Elegir tipo uno a uno{Colors.RESET}")
    print(f"{Colors.WHITE}2. Dejar que la IA decida (automático){Colors.RESET}")
    print()

    type_choice = input(
        f"{Colors.WHITE}Seleccione opción (1-2): {Colors.RESET}"
    ).strip()

    if type_choice not in ("1", "2"):
        print(f"{Colors.RED}Opción inválida. Operación cancelada.{Colors.RESET}")
        return

    ai_decides = type_choice == "2"
    interactive_mode = type_choice == "1"

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
                        f'  {Colors.RED}✗ API Key inválida. Configura con: igv config set OPENAI.key "tu_key"{Colors.RESET}'
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
            # Si viene del flujo de changelogs, aplicar automáticamente sin preguntar
            if skip_changelog_check:
                print(
                    f"{Colors.CYAN}Aplicando {len(processed_commits)} etiquetas...{Colors.RESET}"
                )
                print()
                success = apply_tags(repo, processed_commits, dry_run=False, push=False)
                # No preguntar por push ni por changelog, ya que volveremos al flujo de changelogs
            else:
                # Flujo normal: preguntar al usuario
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
