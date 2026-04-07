"""
Módulo de UI para selección paginada de tags.
"""

from typing import List, Optional
import git
from ..core.ui import (
    Colors,
    clear_screen,
    get_menu_input,
    print_header,
    wait_for_enter,
)


def select_tag_from_list(
    repo: git.Repo, tags: List[git.TagReference], items_per_page: int = 10
) -> Optional[git.TagReference]:
    """Permite al usuario seleccionar un tag de una lista paginada.

    Args:
        repo: Repositorio Git.
        tags: Lista de objetos git.TagReference.
        items_per_page: Cantidad de tags por página.

    Returns:
        Optional[git.TagReference]: Objeto TagReference seleccionado, o None si cancela.
    """
    if not tags:
        print(f"{Colors.YELLOW}No hay tags disponibles para seleccionar.{Colors.RESET}")
        wait_for_enter()
        return None

    total_tags = len(tags)
    total_pages = (total_tags + items_per_page - 1) // items_per_page
    current_page = 1

    while True:
        clear_screen()
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_tags)

        print_header(
            f"SELECCIONAR TAG ({total_tags} encontrados) - Página {current_page}/{total_pages}"
        )
        print()

        for i, tag in enumerate(tags[start_idx:end_idx], start=start_idx + 1):
            tag_commit = tag.commit
            message = tag_commit.message.split("\\n")[0]
            date = tag_commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
            print(
                f"{Colors.CYAN}{i:3}. {tag.name:<15}{Colors.RESET} - {tag_commit.hexsha[:7]} - {date} - {Colors.WHITE}{message}{Colors.RESET}"
            )

        print()
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

        nav_options = []
        if current_page > 1:
            nav_options.append(f"{Colors.YELLOW}p{Colors.WHITE}=anterior")
        if current_page < total_pages:
            nav_options.append(f"{Colors.YELLOW}n{Colors.WHITE}=siguiente")
        nav_options.append(f"{Colors.YELLOW}0{Colors.WHITE}=cancelar")

        print(f"{Colors.WHITE}Navegación: {' | '.join(nav_options)}{Colors.RESET}")
        print(f"{Colors.WHITE}Ingrese número del tag para seleccionar:{Colors.RESET}")

        choice = get_menu_input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()

        if choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif (
            choice == "0"
            or choice == "-back-"
            or choice == "-exit-"
            or choice == "-quit-"
            or choice == ""
        ):
            return None
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < total_tags:
                    return tags[idx]
                else:
                    print(f"{Colors.RED}Número fuera de rango.{Colors.RESET}")
                    wait_for_enter()
            except ValueError:
                pass


__all__ = ["select_tag_from_list"]
