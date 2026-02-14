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
    """Sugiere la siguiente versión basada en el CHANGELOG y tags del repositorio.

    Orden de prioridad (fuente de verdad):
    1. Última versión en CHANGELOG.md (versiones documentadas)
    2. Último tag de Git (si no hay changelog)
    3. 0.0.1 (si no hay ni changelog ni tags)
    """
    try:
        from .git_ops import get_last_tag, parse_version

        # 1. Intentar obtener última versión del CHANGELOG (fuente de verdad principal)
        last_changelog_ver = get_last_changelog_version(repo)

        if last_changelog_ver:
            # Hay versiones en el changelog, sugerir siguiente patch
            major, minor, patch = parse_version(last_changelog_ver)
            return f"{major}.{minor}.{patch + 1}"

        # 2. Si no hay changelog, usar el último tag
        last_tag = get_last_tag(repo)

        if not last_tag:
            # Sin tags ni changelog, sugerir 0.0.1
            return "0.0.1"

        # Extraer número de versión del tag (sin 'v')
        tag_version = last_tag.lstrip("v")
        major, minor, patch = parse_version(tag_version)

        return f"{major}.{minor}.{patch + 1}"
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
        print(f"{Colors.WHITE}  • Último changelog: {last_changelog_ver}{Colors.RESET}")
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
                f"{Colors.YELLOW}⚠ pyproject.toml ({current_version}) está adelantado del changelog ({last_changelog_ver}){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  → Si {current_version} ya está implementado, genera su changelog.{Colors.RESET}"
            )
            has_issues = True
        elif version_tuple(current_version) < version_tuple(last_changelog_ver):
            print(
                f"{Colors.RED}⚠ pyproject.toml ({current_version}) está atrasado del changelog ({last_changelog_ver}){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  → Actualiza pyproject.toml a la versión del changelog.{Colors.RESET}"
            )
            has_issues = True

    # Comparar tag con changelog
    if last_tag_version and last_changelog_ver:
        if version_tuple(last_tag_version) != version_tuple(last_changelog_ver):
            print(
                f"{Colors.YELLOW}⚠ Desincronización entre tag ({last_tag_version}) y changelog ({last_changelog_ver}){Colors.RESET}"
            )
            has_issues = True

    if not has_issues:
        print(f"{Colors.GREEN}✓ Todo sincronizado correctamente.{Colors.RESET}")

    # Obtener versión sugerida
    suggested_version = get_suggested_version(repo, current_version)
    if suggested_version:
        print(
            f"{Colors.WHITE}Versión sugerida: {Colors.GREEN}{suggested_version}{Colors.RESET}"
        )

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
