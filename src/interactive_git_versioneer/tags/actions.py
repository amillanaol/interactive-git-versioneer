"""
Acciones sobre tags para interactive-git-versioneer.

Contiene funciones para crear, eliminar, modificar y sincronizar tags.
"""

import re
from typing import List

import git

from ..core.git_ops import get_last_tag, get_next_version, parse_version
from ..core.models import Commit
from ..core.ui import (
    Colors,
    clear_screen,
    print_header,
    wait_for_enter,
)


def _get_changelog_versions(repo: git.Repo) -> List[str]:
    """Obtiene las versiones registradas en el archivo CHANGELOG.md.

    Args:
        repo: Repositorio Git

    Returns:
        List[str]: Lista de versiones encontradas en el changelog
    """
    import os

    changelog_path = os.path.join(repo.working_dir, "CHANGELOG.md")
    versions = []

    if os.path.exists(changelog_path):
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Buscar todas las versiones en el formato ## [vX.X.X]
            matches = re.findall(r"##\s*\[([^\]]+)\]", content)
            versions = matches
        except Exception:
            pass

    return versions


def apply_tags(
    repo: git.Repo, commits: List[Commit], dry_run: bool = False, push: bool = False
) -> bool:
    """Aplica las etiquetas configuradas a los commits."""
    clear_screen()
    processed_commits = [c for c in commits if c.version_type]

    if not processed_commits:
        print()
        print(
            f"{Colors.YELLOW}No hay commits procesados para aplicar etiquetas.{Colors.RESET}"
        )
        print()
        return False

    # Verificar si el changelog está actualizado
    changelog_versions = _get_changelog_versions(repo)
    last_tag = get_last_tag(repo)

    # Calcular las versiones que se van a crear de manera INCREMENTAL
    # En lugar de calcular cada versión basándose en el repo, calculamos basándonos
    # en la versión anterior calculada en esta misma sesión
    pending_versions = []
    commit_to_version = {}  # Mapeo de commit a versión calculada

    # Obtener la versión base (última versión del repo)
    major, minor, patch = parse_version(last_tag) if last_tag else (0, 0, 0)

    for commit in processed_commits:
        # Calcular siguiente versión basándose en la versión actual (incremental)
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
        pending_versions.append(next_ver)
        commit_to_version[commit.hash] = next_ver  # Guardar la versión calculada

    # Verificar si las versiones pendientes están en el changelog
    missing_in_changelog = []
    for version in pending_versions:
        if version not in changelog_versions:
            missing_in_changelog.append(version)

    if missing_in_changelog:
        # Verificar si el archivo CHANGELOG.md existe
        import os

        changelog_path = os.path.join(repo.working_dir, "CHANGELOG.md")
        changelog_exists = os.path.exists(changelog_path)

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
            f"{Colors.YELLOW}Las siguientes versiones no están registradas en CHANGELOG.md:{Colors.RESET}"
        )
        for version in missing_in_changelog:
            print(f"  {Colors.RED}• {version}{Colors.RESET}")
        print()
        print(
            f"{Colors.YELLOW}Se recomienda realizar el commit correspondiente para no perder los datos actualizados.{Colors.RESET}"
        )
        print()
        if changelog_exists:
            print(
                f"{Colors.YELLOW}El archivo CHANGELOG.md ya existe, será reemplazado.{Colors.RESET}"
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
            return False

        if confirm != "s":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            print(
                f"{Colors.WHITE}Actualice el changelog y vuelva a intentar.{Colors.RESET}"
            )
            return False

        print()

    print_header("APLICANDO ETIQUETAS")

    if dry_run:
        print(
            f"{Colors.YELLOW}[MODO PRUEBA - Los comandos NO serán ejecutados]{Colors.RESET}"
        )

    print()

    success_count = 0
    error_count = 0

    for commit in processed_commits:
        # Usar la versión calculada previamente en lugar de recalcular
        next_ver = commit_to_version[commit.hash]
        message = commit.custom_message or commit.message

        print(
            f"Etiqueta: {Colors.GREEN}{next_ver}{Colors.RESET} | Commit: {Colors.CYAN}{commit.hash[:7]}{Colors.RESET}"
        )

        if dry_run:
            tag_command = f'git tag -a {next_ver} {commit.hash} -m "{message}"'
            print(f"  {Colors.YELLOW}Comando: {tag_command}{Colors.RESET}")
        else:
            try:
                if next_ver in [tag.name for tag in repo.tags]:
                    print(
                        f"  {Colors.YELLOW}⚠️  La etiqueta ya existe, se omite{Colors.RESET}"
                    )
                    continue

                repo.create_tag(next_ver, ref=commit.hash, message=message)
                print(f"  {Colors.GREEN}✓ Etiqueta creada exitosamente{Colors.RESET}")
                success_count += 1

            except Exception as e:
                print(f"  {Colors.RED}✗ Error al crear etiqueta: {e}{Colors.RESET}")
                error_count += 1

        print()

    print_header("RESUMEN")

    if dry_run:
        print(
            f"Se crearían {Colors.YELLOW}{len(processed_commits)}{Colors.RESET} etiquetas"
        )
    else:
        print(
            f"Etiquetas creadas exitosamente: {Colors.GREEN}{success_count}{Colors.RESET}"
        )
        if error_count > 0:
            print(f"Errores: {Colors.RED}{error_count}{Colors.RESET}")

    print()

    if push and not dry_run and success_count > 0:
        print(f"{Colors.CYAN}Subiendo etiquetas al repositorio remoto...{Colors.RESET}")
        try:
            repo.remotes.origin.push(tags=True)
            print(
                f"{Colors.GREEN}✓ Etiquetas subidas exitosamente al remoto{Colors.RESET}"
            )
        except Exception as e:
            print(
                f"{Colors.RED}✗ Error al subir etiquetas al remoto: {e}{Colors.RESET}"
            )

    elif push and dry_run:
        print(
            f"{Colors.YELLOW}[MODO PRUEBA] Se ejecutaría: git push origin --tags{Colors.RESET}"
        )

    if not dry_run and success_count > 0:
        print()
        print_header("ETIQUETAS CREADAS EN ESTA SESIÓN")

        for commit in processed_commits:
            # Usar la versión calculada previamente en lugar de recalcular
            next_ver = commit_to_version[commit.hash]
            print(f"  {next_ver}")

        print()

    return True


def change_last_tag(repo: git.Repo) -> bool:
    """Cambia el último tag del repositorio.

    Permite modificar la versión del último tag creado para corregir o
    asignar otra versión (ej: 1.0.0 para un primer release).

    Args:
        repo: Repositorio Git

    Returns:
        bool: True si fue exitoso, False en caso de error
    """
    try:
        clear_screen()
        print_header("CAMBIAR ÚLTIMO TAG")

        last_tag = get_last_tag(repo)

        if not last_tag:
            print()
            print(f"{Colors.YELLOW}No hay tags en el repositorio.{Colors.RESET}")
            print(
                f"{Colors.YELLOW}Cree el primer tag usando la opción de procesar commits.{Colors.RESET}"
            )
            print()
            return False

        print()
        print(f"{Colors.WHITE}Etiqueta actual:{Colors.RESET}")
        try:
            tag_obj = repo.tags[last_tag]
            commit = tag_obj.commit
            print(f"  {Colors.GREEN}Tag:{Colors.RESET} {last_tag}")
            print(f"  {Colors.CYAN}Commit:{Colors.RESET} {commit.hexsha[:7]}")
            print(
                f"  {Colors.CYAN}Mensaje:{Colors.RESET} {tag_obj.tag.message.strip() if tag_obj.tag else 'N/A'}"
            )
        except Exception as e:
            print(
                f"{Colors.RED}Error al obtener información del tag: {e}{Colors.RESET}"
            )
            return False

        print()
        print(f"{Colors.YELLOW}¿Desea cambiar este tag?{Colors.RESET}")
        confirm = (
            input(f"{Colors.WHITE}¿Continuar? (s/n): {Colors.RESET}").strip().lower()
        )

        if confirm != "s":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return False

        print()
        new_version = input(
            f"{Colors.WHITE}Ingrese la nueva versión (ej: v1.0.0, 2.1.0): {Colors.RESET}"
        ).strip()

        if not new_version:
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return False

        if not new_version.startswith("v"):
            new_version = f"v{new_version}"

        if not re.match(r"^v\d+\.\d+\.\d+", new_version):
            print(
                f"{Colors.RED}Formato de versión inválido. Use: v<major>.<minor>.<patch>{Colors.RESET}"
            )
            return False

        print()
        current_message = tag_obj.tag.message.strip() if tag_obj.tag else "N/A"
        print(
            f"{Colors.WHITE}Mensaje actual:{Colors.RESET} {Colors.CYAN}{current_message}{Colors.RESET}"
        )
        new_message = input(
            f"{Colors.WHITE}Ingrese mensaje para el nuevo tag (Enter para usar el actual): {Colors.RESET}"
        ).strip()

        if not new_message:
            new_message = current_message if current_message != "N/A" else last_tag

        print()
        print(f"{Colors.YELLOW}Resumen del cambio:{Colors.RESET}")
        print(f"  {Colors.RED}Eliminar:{Colors.RESET} {last_tag}")
        print(f"  {Colors.GREEN}Crear:{Colors.RESET} {new_version}")
        print(f"  {Colors.CYAN}Mensaje:{Colors.RESET} {new_message}")
        print()

        confirm_change = (
            input(f"{Colors.YELLOW}¿Confirmar el cambio? (s/n): {Colors.RESET}")
            .strip()
            .lower()
        )

        if confirm_change != "s":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return False

        try:
            print()
            print(f"{Colors.CYAN}Eliminando tag antiguo...{Colors.RESET}")
            repo.delete_tag(last_tag)
            print(f"{Colors.GREEN}✓ Tag {last_tag} eliminado{Colors.RESET}")

            print(f"{Colors.CYAN}Creando nuevo tag...{Colors.RESET}")
            repo.create_tag(new_version, ref=commit.hexsha, message=new_message)
            print(
                f"{Colors.GREEN}✓ Tag {new_version} creado exitosamente{Colors.RESET}"
            )

            print()
            print(f"{Colors.GREEN}✓ Tag cambiado exitosamente{Colors.RESET}")
            print()
            return True

        except Exception as e:
            print(f"{Colors.RED}✗ Error al cambiar tag: {e}{Colors.RESET}")
            print(
                f"{Colors.YELLOW}Puede que necesite restaurar el tag eliminado.{Colors.RESET}"
            )
            return False
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        return False


def clean_all_tags(repo: git.Repo, include_remote: bool = True) -> bool:
    """Elimina todos los tags locales y opcionalmente remotos.

    ADVERTENCIA: Esta es una operación destructiva e irreversible.

    Args:
        repo: Repositorio Git
        include_remote: Si True, también elimina los tags del remoto

    Returns:
        bool: True si fue exitoso, False en caso de error o cancelación
    """
    clear_screen()
    print_header("LIMPIAR TODOS LOS TAGS")

    print()
    print(
        f"{Colors.RED}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}"
    )
    print(
        f"{Colors.RED}║  ⚠️  ADVERTENCIA: OPERACIÓN DESTRUCTIVA E IRREVERSIBLE  ⚠️   ║{Colors.RESET}"
    )
    print(
        f"{Colors.RED}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}"
    )
    print()

    local_tags = list(repo.tags)
    if not local_tags:
        print(f"{Colors.YELLOW}No hay tags locales en este repositorio.{Colors.RESET}")
        print()
        return False

    print(
        f"{Colors.WHITE}Tags locales que se eliminarán ({len(local_tags)}):{Colors.RESET}"
    )
    sorted_tags = sorted(local_tags, key=lambda t: parse_version(t.name), reverse=True)
    for tag in sorted_tags[:10]:
        print(f"  {Colors.CYAN}- {tag.name}{Colors.RESET}")
    if len(sorted_tags) > 10:
        print(f"  {Colors.YELLOW}... y {len(sorted_tags) - 10} más{Colors.RESET}")
    print()

    remote_tags_count = 0
    if include_remote:
        try:
            if repo.remotes:
                origin = (
                    repo.remotes.origin
                    if hasattr(repo.remotes, "origin")
                    else repo.remotes[0]
                )
                ls_remote_output = repo.git.ls_remote("--tags", origin.name)
                if ls_remote_output:
                    remote_tags_count = len(
                        [
                            line
                            for line in ls_remote_output.split("\n")
                            if line.strip() and not line.endswith("^{}")
                        ]
                    )
                print(
                    f"{Colors.WHITE}Tags remotos que se eliminarán: ~{remote_tags_count}{Colors.RESET}"
                )
                print()
        except Exception as e:
            print(
                f"{Colors.YELLOW}No se pudo verificar tags remotos: {e}{Colors.RESET}"
            )
            print()

    print(
        f"{Colors.YELLOW}Esta acción eliminará TODOS los tags y no se puede deshacer.{Colors.RESET}"
    )
    print(f"{Colors.YELLOW}Deberá rehacer el versionado desde cero.{Colors.RESET}")
    print()

    try:
        confirm1 = (
            input(
                f"{Colors.WHITE}¿Está seguro que desea continuar? (escriba 'si' para confirmar): {Colors.RESET}"
            )
            .strip()
            .lower()
        )
        if confirm1 != "si":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return False

        print()
        confirm2 = input(
            f"{Colors.RED}ÚLTIMA CONFIRMACIÓN - ¿Eliminar {len(local_tags)} tags locales{' y remotos' if include_remote else ''}? (escriba 'ELIMINAR'): {Colors.RESET}"
        ).strip()
        if confirm2 != "ELIMINAR":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return False

    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        return False

    print()
    print(f"{Colors.CYAN}Eliminando tags...{Colors.RESET}")
    print()

    local_deleted = 0
    local_errors = 0
    for tag in local_tags:
        try:
            repo.delete_tag(tag.name)
            print(f"  {Colors.GREEN}✓ Local: {tag.name}{Colors.RESET}")
            local_deleted += 1
        except Exception as e:
            print(f"  {Colors.RED}✗ Local: {tag.name} - {e}{Colors.RESET}")
            local_errors += 1

    remote_deleted = 0
    remote_errors = 0
    if include_remote and repo.remotes:
        print()
        print(f"{Colors.CYAN}Eliminando tags remotos...{Colors.RESET}")
        print()

        try:
            origin = (
                repo.remotes.origin
                if hasattr(repo.remotes, "origin")
                else repo.remotes[0]
            )

            ls_remote_output = repo.git.ls_remote("--tags", origin.name)
            if ls_remote_output:
                remote_tag_names = []
                for line in ls_remote_output.split("\n"):
                    if not line.strip() or line.endswith("^{}"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        ref_path = parts[1]
                        if ref_path.startswith("refs/tags/"):
                            tag_name = ref_path.replace("refs/tags/", "")
                            remote_tag_names.append(tag_name)

                for tag_name in remote_tag_names:
                    try:
                        repo.git.push(origin.name, "--delete", f"refs/tags/{tag_name}")
                        print(f"  {Colors.GREEN}✓ Remoto: {tag_name}{Colors.RESET}")
                        remote_deleted += 1
                    except Exception as e:
                        print(f"  {Colors.RED}✗ Remoto: {tag_name} - {e}{Colors.RESET}")
                        remote_errors += 1

        except Exception as e:
            print(f"{Colors.RED}Error al eliminar tags remotos: {e}{Colors.RESET}")

    print()
    print_header("RESUMEN DE LIMPIEZA")
    print(f"Tags locales eliminados: {Colors.GREEN}{local_deleted}{Colors.RESET}")
    if local_errors > 0:
        print(f"Errores locales: {Colors.RED}{local_errors}{Colors.RESET}")

    if include_remote:
        print(f"Tags remotos eliminados: {Colors.GREEN}{remote_deleted}{Colors.RESET}")
        if remote_errors > 0:
            print(f"Errores remotos: {Colors.RED}{remote_errors}{Colors.RESET}")

    print()
    print(
        f"{Colors.GREEN}✓ Limpieza completada. Puede comenzar el versionado desde cero.{Colors.RESET}"
    )
    print()

    return True


def sync_tags_from_remote(repo: git.Repo) -> bool:
    """Sincroniza tags desde el repositorio remoto al local.

    Descarga los tags que existen en el remoto pero no localmente.

    Args:
        repo: Repositorio Git

    Returns:
        bool: True si fue exitoso, False en caso de error
    """
    clear_screen()
    print_header("SINCRONIZAR TAGS DESDE REMOTO")

    try:
        remote = repo.remotes.origin
    except AttributeError:
        print(
            f"{Colors.RED}Error: No hay un remoto 'origin' configurado.{Colors.RESET}"
        )
        return False

    print(f"{Colors.CYAN}Obteniendo tags del repositorio remoto...{Colors.RESET}")
    print()

    try:
        local_tags_before = set(tag.name for tag in repo.tags)

        repo.git.fetch(remote.name, "--tags", "--force")

        local_tags_after = set(tag.name for tag in repo.tags)
        new_tags = local_tags_after - local_tags_before

        if new_tags:
            print(f"{Colors.GREEN}✓ Tags sincronizados exitosamente{Colors.RESET}")
            print()
            print(
                f"{Colors.WHITE}Nuevos tags descargados ({len(new_tags)}):{Colors.RESET}"
            )
            for tag in sorted(new_tags, key=parse_version):
                print(f"  {Colors.GREEN}+ {tag}{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}✓ Sincronización completada{Colors.RESET}")
            print(f"{Colors.WHITE}No hay tags nuevos en el remoto.{Colors.RESET}")

        print()
        print(
            f"{Colors.WHITE}Total de tags locales: {len(local_tags_after)}{Colors.RESET}"
        )
        return True

    except Exception as e:
        print(f"{Colors.RED}✗ Error al sincronizar tags: {e}{Colors.RESET}")
        return False


def push_tags_to_remote(repo: git.Repo, page_size: int = 15) -> bool:
    """Sube todas las etiquetas al repositorio remoto con paginación.

    Args:
        repo: Repositorio Git
        page_size: Número de tags a mostrar por página (default: 15)

    Returns:
        bool: True si fue exitoso, False en caso de error
    """
    clear_screen()
    print_header("SUBIR TAGS A GITHUB")

    try:
        remote = repo.remotes.origin
    except AttributeError:
        print(
            f"{Colors.RED}Error: No hay un remoto 'origin' configurado.{Colors.RESET}"
        )
        return False

    local_tags = sorted(repo.tags, key=lambda t: parse_version(t.name))
    if not local_tags:
        print(f"{Colors.YELLOW}No hay tags locales para subir.{Colors.RESET}")
        return False

    total_tags = len(local_tags)

    # Paginación del listado
    current_page = 0
    tags_shown = 0

    while tags_shown < total_tags:
        # Calcular rango de tags para esta página
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_tags)

        # Mostrar tags de la página actual
        print(f"{Colors.WHITE}Tags locales encontrados:{Colors.RESET}")
        for i in range(start_idx, end_idx):
            print(f"  - {local_tags[i].name}")

        tags_shown = end_idx
        current_page += 1

        # Si quedan más tags por mostrar
        if tags_shown < total_tags:
            remaining = total_tags - tags_shown
            print()
            print(
                f"{Colors.CYAN}Mostrados {tags_shown} de {total_tags} tags "
                f"({remaining} más)...{Colors.RESET}"
            )
            print()
            print(
                f"{Colors.YELLOW}Opciones: "
                f"{Colors.WHITE}[Enter]{Colors.YELLOW} ver más, "
                f"{Colors.WHITE}[s]{Colors.YELLOW} subir todos, "
                f"{Colors.WHITE}[c]{Colors.YELLOW} cancelar{Colors.RESET}"
            )
            choice = (
                input(f"{Colors.WHITE}¿Qué desea hacer? {Colors.RESET}").strip().lower()
            )

            if choice == "c":
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                return False
            elif choice == "s":
                break
            # Si presiona Enter u otra cosa, continúa mostrando más tags
        else:
            # Se mostraron todos los tags
            print()

    print(f"{Colors.YELLOW}¿Desea subir todos los tags al remoto?{Colors.RESET}")
    confirm = input(f"{Colors.WHITE}¿Continuar? (s/n): {Colors.RESET}").strip().lower()

    if confirm != "s":
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        return False

    print()
    print(
        f"{Colors.CYAN}Subiendo {total_tags} tags al repositorio remoto...{Colors.RESET}"
    )

    try:
        remote.push(tags=True)
        print(f"{Colors.GREEN}✓ Tags subidos exitosamente a GitHub{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Error al subir tags: {e}{Colors.RESET}")
        return False
