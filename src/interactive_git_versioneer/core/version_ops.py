import re
from pathlib import Path
from typing import Optional

from .ui import Colors, clear_screen, wait_for_enter


def version_tuple(v: str) -> tuple:
    """Convierte string de versión a tupla de integers para comparación."""
    try:
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    except:
        return (0, 0, 0)


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
    """Sugiere la siguiente versión basada en el último tag del repositorio.

    Si la versión actual del pyproject.toml es mayor que el último tag,
    usa esa como base para calcular la sugerencia.
    """
    try:
        from .git_ops import get_last_tag, get_next_version

        last_tag = get_last_tag(repo)

        # Determinar versión base: usar la mayor entre el tag y pyproject.toml
        base_version = current_version
        if last_tag:
            # Extraer número de versión del tag (sin 'v')
            tag_version = last_tag.lstrip("v")

            if version_tuple(base_version) > version_tuple(tag_version):
                # pyproject tiene versión más alta, usarla como base y calcular siguiente
                # sobre esa versión
                try:
                    parts = base_version.split(".")
                    if len(parts) >= 3:
                        parts[2] = str(int(parts[2]) + 1)
                        return ".".join(parts[:3])
                except:
                    pass

        # Caso normal: usar el tag como base
        suggested = get_next_version(repo, "patch")
        if suggested and suggested.startswith("v"):
            suggested = suggested[1:]

        return suggested
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

    # Obtener último tag para comparación
    from .git_ops import get_last_tag

    last_tag = get_last_tag(repo)
    last_tag_version = last_tag.lstrip("v") if last_tag else None

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

    # Advertir si hay inconsistencia entre pyproject y tags
    if last_tag_version:
        if version_tuple(current_version) > version_tuple(last_tag_version):
            print(
                f"{Colors.RED}⚠ Advertencia: pyproject.toml ({current_version}) está por "
                f"delante del último tag ({last_tag}).{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}  El tag {last_tag} existe pero pyproject tiene versión mayor.{Colors.RESET}"
            )
        elif version_tuple(current_version) < version_tuple(last_tag_version):
            print(
                f"{Colors.RED}⚠ Advertencia: pyproject.toml ({current_version}) está por "
                f"detrás del último tag ({last_tag}).{Colors.RESET}"
            )
        else:
            print(f"{Colors.WHITE}Último tag: {Colors.GREEN}{last_tag}{Colors.RESET}")

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
