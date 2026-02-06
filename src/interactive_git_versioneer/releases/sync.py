"""Sincronización local↔remoto de tags."""

import subprocess
from typing import Set

import git

from ..core.git_ops import parse_version
from ..core.ui import Colors, clear_screen, print_header, wait_for_enter


def sync_with_remote(repo: git.Repo) -> None:
    """Sincroniza tags y releases con el repositorio remoto.

    Args:
        repo: Repositorio Git
    """
    clear_screen()
    print_header("SINCRONIZAR CON REMOTO")

    # Verificar si hay remoto configurado
    try:
        remote = repo.remotes.origin
    except AttributeError:
        print(
            f"{Colors.RED}Error: No hay un remoto 'origin' configurado.{Colors.RESET}"
        )
        wait_for_enter()
        return

    print(f"{Colors.CYAN}Obteniendo información del remoto...{Colors.RESET}")
    print()

    # Fetch para obtener tags remotos
    try:
        remote.fetch(tags=True)
        print(f"{Colors.GREEN}✓ Tags remotos actualizados{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error al obtener tags remotos: {e}{Colors.RESET}")

    print()

    # Obtener tags locales
    local_tags: Set[str] = set(t.name for t in repo.tags)

    # Obtener tags remotos usando git ls-remote
    remote_tags: Set[str] = set()
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin"],
            capture_output=True,
            text=True,
            check=False,
            cwd=repo.working_dir,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line and "refs/tags/" in line:
                    tag_ref = line.split("refs/tags/")[-1]
                    # Ignorar refs que terminan en ^{} (annotated tag dereference)
                    if not tag_ref.endswith("^{}"):
                        remote_tags.add(tag_ref)
    except Exception as e:
        print(
            f"{Colors.YELLOW}Advertencia: No se pudieron listar tags remotos: {e}{Colors.RESET}"
        )

    # Calcular diferencias
    only_local = local_tags - remote_tags
    only_remote = remote_tags - local_tags
    in_both = local_tags & remote_tags

    # Mostrar resumen
    print(f"{Colors.WHITE}═══ RESUMEN DE SINCRONIZACIÓN ═══{Colors.RESET}")
    print()
    print(
        f"{Colors.GREEN}Tags sincronizados (local y remoto): {len(in_both)}{Colors.RESET}"
    )

    if only_local:
        print()
        print(f"{Colors.YELLOW}Tags solo en LOCAL ({len(only_local)}):{Colors.RESET}")
        for tag in sorted(only_local, key=lambda t: parse_version(t), reverse=True)[
            :10
        ]:
            print(f"  ↑ {tag}")
        if len(only_local) > 10:
            print(f"  ... y {len(only_local) - 10} más")

    if only_remote:
        print()
        print(f"{Colors.CYAN}Tags solo en REMOTO ({len(only_remote)}):{Colors.RESET}")
        for tag in sorted(only_remote, key=lambda t: parse_version(t), reverse=True)[
            :10
        ]:
            print(f"  ↓ {tag}")
        if len(only_remote) > 10:
            print(f"  ... y {len(only_remote) - 10} más")

    print()

    # Opciones de sincronización
    if only_local or only_remote:
        print(f"{Colors.WHITE}Opciones de sincronización:{Colors.RESET}")
        print(f"  1. Subir tags locales al remoto (push)")
        print(f"  2. Descargar tags remotos al local (fetch)")
        print(f"  3. Sincronización completa (push + fetch)")
        print(f"  0. Cancelar")
        print()

        choice = input(f"{Colors.WHITE}Seleccione opción: {Colors.RESET}").strip()

        if choice == "1" and only_local:
            print()
            print(
                f"{Colors.CYAN}Subiendo {len(only_local)} tags al remoto...{Colors.RESET}"
            )
            try:
                remote.push(tags=True)
                print(f"{Colors.GREEN}✓ Tags subidos exitosamente{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}✗ Error al subir tags: {e}{Colors.RESET}")

        elif choice == "2" and only_remote:
            print()
            print(f"{Colors.CYAN}Descargando tags del remoto...{Colors.RESET}")
            try:
                remote.fetch(tags=True)
                print(f"{Colors.GREEN}✓ Tags descargados exitosamente{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}✗ Error al descargar tags: {e}{Colors.RESET}")

        elif choice == "3":
            print()
            # Push primero
            if only_local:
                print(f"{Colors.CYAN}Subiendo tags al remoto...{Colors.RESET}")
                try:
                    remote.push(tags=True)
                    print(f"{Colors.GREEN}✓ Tags subidos exitosamente{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}✗ Error al subir tags: {e}{Colors.RESET}")

            # Luego fetch
            print(f"{Colors.CYAN}Descargando tags del remoto...{Colors.RESET}")
            try:
                remote.fetch(tags=True)
                print(f"{Colors.GREEN}✓ Tags descargados exitosamente{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}✗ Error al descargar tags: {e}{Colors.RESET}")

        elif choice == "0":
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        else:
            print(
                f"{Colors.YELLOW}Opción no válida o no hay tags para esa operación.{Colors.RESET}"
            )
    else:
        print(
            f"{Colors.GREEN}✓ Todo está sincronizado. No hay acciones pendientes.{Colors.RESET}"
        )

    wait_for_enter()
