import os
import re
from pathlib import Path
from typing import List, Optional

from .ui import Colors, clear_screen, wait_for_enter


def version_tuple(v: str) -> tuple:
    """Convierte string de versión a tupla de integers para comparación."""
    try:
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    except:
        return (0, 0, 0)


def get_changelog_versions(repo: "git.Repo") -> List[str]:
    """Obtiene las versiones registradas en el archivo CHANGELOG.md.

    Args:
        repo: Repositorio Git

    Returns:
        List[str]: Lista de versiones encontradas en el changelog (excluyendo "Unreleased")
    """
    changelog_path = os.path.join(repo.working_dir, "CHANGELOG.md")
    versions = []

    if os.path.exists(changelog_path):
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Buscar todas las versiones en el formato ## [vX.X.X] o ## [X.X.X]
            matches = re.findall(r"##\s*\[([^\]]+)\]", content)
            # Filtrar "Unreleased" (entrada temporal para commits pendientes)
            versions = [v for v in matches if v.lower() != "unreleased"]
        except Exception:
            pass

    return versions


def get_last_changelog_version(repo: "git.Repo") -> Optional[str]:
    """Obtiene la última versión registrada en el CHANGELOG.md.

    Args:
        repo: Repositorio Git

    Returns:
        Optional[str]: Última versión en el changelog, o None si no hay
    """
    versions = get_changelog_versions(repo)
    if versions:
        # La primera versión en el changelog es la más reciente
        return versions[0].lstrip("v")
    return None


def get_current_version(repo_root: Path) -> Optional[str]:
    """Reads the current version from pyproject.toml."""
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'^version\s*=\s*"(.*)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def update_version_in_pyproject(repo_root: Path, new_version: str) -> bool:
    """Updates the version in pyproject.toml."""
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        print(
            f"{Colors.RED}Error: pyproject.toml no encontrado en {repo_root}{Colors.RESET}"
        )
        return False

    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    updated = False
    with open(pyproject_path, "w", encoding="utf-8") as f:
        for line in content:
            if re.match(r'^version\s*=\s*".*"', line):
                f.write(f'version = "{new_version}"\n')
                updated = True
            else:
                f.write(line)
    return updated


def is_valid_semver(version_str: str) -> bool:
    """Checks if a string is a valid semantic version."""
    # Basic semantic versioning check (e.g., 1.0.0, 1.2.3-alpha.1+build.2)
    semver_pattern = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )
    return bool(semver_pattern.match(version_str))


def get_suggested_version(repo: "git.Repo", current_version: str) -> Optional[str]:
    """Sugiere la versión para sincronizar pyproject.toml con el CHANGELOG.

    pyproject.toml debe estar sincronizado con el CHANGELOG, NO adelantado.

    Orden de prioridad (fuente de verdad):
    1. Última versión en CHANGELOG.md (versión a sincronizar)
    2. Último tag de Git (si no hay changelog)
    3. 0.0.1 (si no hay ni changelog ni tags)
    """
    try:
        from .git_ops import get_last_tag

        # 1. Intentar obtener última versión del CHANGELOG (fuente de verdad principal)
        last_changelog_ver = get_last_changelog_version(repo)

        if last_changelog_ver:
            # Sugerir la MISMA versión del changelog (sincronizar, no adelantar)
            return last_changelog_ver

        # 2. Si no hay changelog, usar el último tag
        last_tag = get_last_tag(repo)

        if not last_tag:
            # Sin tags ni changelog, sugerir 0.0.1
            return "0.0.1"

        # Sugerir la versión del último tag (sincronizar)
        return last_tag.lstrip("v")
    except Exception:
        pass

    return None


def action_update_project_version(repo: "git.Repo") -> bool:
    """
    Permite al usuario actualizar la versión del proyecto en pyproject.toml.
    Sugiere automáticamente la siguiente versión basada en el último tag.
    """
    clear_screen()
    print(f"{Colors.CYAN}--- ACTUALIZAR VERSIÓN DEL PROYECTO ---{Colors.RESET}")

    repo_root = Path(repo.working_dir)
    current_version = get_current_version(repo_root)

    # Obtener último tag y última versión del changelog para comparación
    from .git_ops import get_last_tag

    last_tag = get_last_tag(repo)
    last_tag_version = last_tag.lstrip("v") if last_tag else None
    last_changelog_ver = get_last_changelog_version(repo)

    if current_version:
        print(
            f"{Colors.WHITE}Versión actual en pyproject.toml: {Colors.YELLOW}{current_version}{Colors.RESET}"
        )
    else:
        print(
            f"{Colors.YELLOW}No se encontró la versión actual en pyproject.toml.{Colors.RESET}"
        )
        wait_for_enter()
        return False

    # Mostrar estado del ecosistema de versiones
    print()
    print(f"{Colors.CYAN}Estado del versionado:{Colors.RESET}")

    # Mostrar último changelog
    if last_changelog_ver:
        changelog_versions = get_changelog_versions(repo)
        num_versions = len(changelog_versions)
        print(
            f"{Colors.WHITE}  • Último changelog: {last_changelog_ver} ({num_versions} versiones registradas){Colors.RESET}"
        )
    else:
        print(f"{Colors.WHITE}  • Último changelog: {Colors.YELLOW}(ninguno){Colors.RESET}")

    # Mostrar último tag
    if last_tag_version:
        print(f"{Colors.WHITE}  • Último tag: {last_tag_version}{Colors.RESET}")
    else:
        print(f"{Colors.WHITE}  • Último tag: {Colors.YELLOW}(ninguno){Colors.RESET}")

    print(f"{Colors.WHITE}  • pyproject.toml: {current_version}{Colors.RESET}")

    # Advertir si hay inconsistencias
    print()
    has_issues = False

    # Comparar changelog con pyproject
    if last_changelog_ver:
        if version_tuple(current_version) > version_tuple(last_changelog_ver):
            print(
                f"{Colors.RED}⚠ DESINCRONIZACIÓN: pyproject.toml ({current_version}) adelantado del CHANGELOG ({last_changelog_ver}){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  → ESTO NO DEBE PASAR. El CHANGELOG es la fuente de verdad.{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}  → Opciones:{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}     a) Retroceder pyproject.toml a {last_changelog_ver}{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}     b) Etiquetar y generar changelog para {current_version}{Colors.RESET}"
            )
            has_issues = True
        elif version_tuple(current_version) < version_tuple(last_changelog_ver):
            print(
                f"{Colors.YELLOW}⚠ pyproject.toml ({current_version}) está atrasado del CHANGELOG ({last_changelog_ver}){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  → Actualiza pyproject.toml a {last_changelog_ver} (versión sugerida).{Colors.RESET}"
            )
            has_issues = True
        else:
            # Versiones iguales entre pyproject y changelog
            print(f"{Colors.GREEN}✓ pyproject.toml sincronizado con CHANGELOG.{Colors.RESET}")

    # Comparar tag con changelog
    if last_tag_version and last_changelog_ver:
        if version_tuple(last_tag_version) > version_tuple(last_changelog_ver):
            print(
                f"{Colors.YELLOW}⚠ Tag ({last_tag_version}) adelantado del CHANGELOG ({last_changelog_ver}){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  → Genera el changelog para el tag {last_tag}.{Colors.RESET}"
            )
            has_issues = True
        elif version_tuple(last_tag_version) < version_tuple(last_changelog_ver):
            print(
                f"{Colors.YELLOW}⚠ CHANGELOG ({last_changelog_ver}) adelantado del último tag ({last_tag_version}){Colors.RESET}"
            )
            has_issues = True

    # Obtener versión sugerida
    suggested_version = get_suggested_version(repo, current_version)
    if suggested_version:
        print(
            f"{Colors.WHITE}Versión sugerida: {Colors.GREEN}{suggested_version}{Colors.RESET}"
        )

    print()

    # Advertencia importante sobre el flujo correcto
    print(f"{Colors.CYAN}FLUJO RECOMENDADO:{Colors.RESET}")
    print(f"{Colors.WHITE}  1. Etiquetar commits (menú Tags){Colors.RESET}")
    print(f"{Colors.WHITE}  2. Generar changelog (menú Releases → Changelogs){Colors.RESET}")
    print(f"{Colors.WHITE}  3. Actualizar pyproject.toml (esta opción){Colors.RESET}")
    print()

    while True:
        if suggested_version:
            prompt = f"{Colors.WHITE}Nueva versión [{Colors.GREEN}{suggested_version}{Colors.WHITE}] (o 'c' para cancelar): {Colors.RESET}"
        else:
            prompt = f"{Colors.WHITE}Introduce la nueva versión (o 'c' para cancelar): {Colors.RESET}"

        new_version = input(prompt).strip()

        # Si el usuario presiona Enter y hay sugerencia, usar la sugerida
        if not new_version and suggested_version:
            new_version = suggested_version

        if new_version.lower() == "c":
            print(f"{Colors.YELLOW}Actualización de versión cancelada.{Colors.RESET}")
            wait_for_enter()
            return False

        if not new_version:
            print(f"{Colors.RED}Error: Debes introducir una versión.{Colors.RESET}")
            continue

        if not is_valid_semver(new_version):
            print(
                f"{Colors.RED}Error: La versión introducida no es un formato SemVer válido (ej. 1.0.0, 1.2.3-alpha.1).{Colors.RESET}"
            )
            continue

        if new_version == current_version:
            print(
                f"{Colors.YELLOW}La nueva versión es igual a la actual. Por favor, introduce una versión diferente.{Colors.RESET}"
            )
            continue

        # VALIDACIÓN CRÍTICA: Verificar que la versión exista en el CHANGELOG
        if last_changelog_ver:
            new_version_stripped = new_version.lstrip("v")
            changelog_versions = get_changelog_versions(repo)
            # Normalizar versiones del changelog (quitar 'v' si existe)
            changelog_versions_normalized = [v.lstrip("v") for v in changelog_versions]

            # Verificar si la nueva versión está en el changelog
            version_in_changelog = new_version_stripped in changelog_versions_normalized

            # Verificar si la nueva versión está adelantada del changelog
            if version_tuple(new_version_stripped) > version_tuple(last_changelog_ver):
                print()
                print(f"{Colors.RED}⚠️  ERROR: La versión {new_version} NO está en el CHANGELOG{Colors.RESET}")
                print(f"{Colors.WHITE}   Última versión en CHANGELOG: {last_changelog_ver}{Colors.RESET}")
                print()
                print(f"{Colors.YELLOW}   pyproject.toml NO debe estar adelantado del CHANGELOG.{Colors.RESET}")
                print()
                print(f"{Colors.WHITE}   Sigue el flujo correcto:{Colors.RESET}")
                print(f"{Colors.WHITE}   1. Etiqueta commits: igv → Menú Tags → Etiquetar commits{Colors.RESET}")
                print(f"{Colors.WHITE}   2. Genera changelog: igv → Menú Releases → Changelogs → Continuar changelog{Colors.RESET}")
                print(f"{Colors.WHITE}   3. Actualiza pyproject.toml: igv → Menú Releases → Actualizar versión{Colors.RESET}")
                print()

                try:
                    override = input(
                        f"{Colors.YELLOW}¿Actualizar de todos modos? (NO recomendado) (s/n): {Colors.RESET}"
                    ).strip().lower()
                except KeyboardInterrupt:
                    print()
                    print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                    wait_for_enter()
                    return False

                if override != "s":
                    print(f"{Colors.GREEN}Operación cancelada. Sigue el flujo recomendado.{Colors.RESET}")
                    wait_for_enter()
                    return False
            elif not version_in_changelog and new_version_stripped != last_changelog_ver:
                # La versión no está en el changelog pero no está adelantada (versión antigua)
                print()
                print(f"{Colors.YELLOW}⚠️  Advertencia: La versión {new_version} no está en el CHANGELOG{Colors.RESET}")
                print(f"{Colors.WHITE}   ¿Estás seguro de retroceder a una versión no documentada?{Colors.RESET}")
                print()

                try:
                    confirm = input(
                        f"{Colors.WHITE}¿Continuar? (s/n): {Colors.RESET}"
                    ).strip().lower()
                except KeyboardInterrupt:
                    print()
                    print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                    wait_for_enter()
                    return False

                if confirm != "s":
                    print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                    wait_for_enter()
                    return False

        break

    if update_version_in_pyproject(repo_root, new_version):
        print()
        print(
            f"{Colors.GREEN}✓ Versión actualizada a {new_version} en pyproject.toml.{Colors.RESET}"
        )
        print(f"{Colors.YELLOW}Recuerda hacer commit de este cambio.{Colors.RESET}")
    else:
        print(f"{Colors.RED}No se pudo actualizar la versión.{Colors.RESET}")

    wait_for_enter()
    return False
