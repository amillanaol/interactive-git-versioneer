"""
Módulo de interfaz de usuario para interactive-git-tagger.

Contiene clases y funciones reutilizables para la UI del terminal.
"""

import os
import platform
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional

# Importar módulos para captura de teclas según el SO
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty


def clear_screen() -> None:
    """Limpia la pantalla de la consola.

    Funciona en Windows, Linux y macOS.
    """
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


# ===========================
# DEFINICIONES DE COLORES
# ===========================


class Colors:
    """Códigos ANSI para colores en terminal"""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# ===========================
# CONFIGURACIÓN UI
# ===========================

MENU_WIDTH = 60  # Ancho estándar para menús y encabezados

# ===========================
# FUNCIONES DE UI
# ===========================


def print_header(title: str, width: int = MENU_WIDTH) -> None:
    """Imprime un encabezado formateado.

    Args:
        title: Título del encabezado
        width: Ancho del encabezado (default: MENU_WIDTH)
    """
    print()
    print(f"{Colors.CYAN}{'═' * width}{Colors.RESET}")
    if title:
        print(f"{Colors.CYAN}{title.center(width)}{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * width}{Colors.RESET}")


def print_subheader(title: str, width: int = MENU_WIDTH) -> None:
    """Imprime un subencabezado formateado.

    Args:
        title: Título del subencabezado
        width: Ancho del subencabezado (default: MENU_WIDTH)
    """
    print()
    print(f"{Colors.WHITE}{'─' * width}{Colors.RESET}")
    print(f"{Colors.WHITE}{title}{Colors.RESET}")
    print(f"{Colors.WHITE}{'─' * width}{Colors.RESET}")


def print_info(label: str, value: str, color: str = None) -> None:
    """Imprime una línea de información formateada.

    Args:
        label: Etiqueta de la información
        value: Valor a mostrar
        color: Color para el valor (default: Colors.CYAN)
    """
    if color is None:
        color = Colors.CYAN
    print(f"{Colors.WHITE}{label:<15}{Colors.RESET}{color}{value}{Colors.RESET}")


def wait_for_enter() -> None:
    """Espera a que el usuario presione Enter."""
    try:
        input(f"{Colors.WHITE}Presione Enter para continuar{Colors.RESET}")
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")


def wait_for_enter_or_skip(skip_hint: bool = True) -> str:
    """Espera a que el usuario presione Enter, Ctrl+X para saltar, o Ctrl+A para permitir todos.

    Args:
        skip_hint: Si True, muestra el hint de opciones

    Returns:
        str: "continue" si presiona Enter
             "skip" si Ctrl+X/Esc
             "all" si Ctrl+A (permitir todos los siguientes)
             "quit" si q (salir del programa)
             "cancel" si Ctrl+C
    """
    if skip_hint:
        print(
            f"{Colors.CYAN}[Enter: continuar | Ctrl+A: permitir todos | Ctrl+X: saltar resto | q: salir]{Colors.RESET}"
        )

    try:
        if platform.system() == "Windows":
            return _wait_windows()
        else:
            return _wait_unix()
    except KeyboardInterrupt:
        print()
        return "cancel"


def _wait_windows() -> str:
    """Espera tecla en Windows."""
    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwch()

            # Enter
            if char in ("\r", "\n"):
                print()
                return "continue"

            # Ctrl+A (código 0x01) - Permitir todos
            if char == "\x01":
                print()
                return "all"

            # Ctrl+X (código 0x18) - Saltar resto
            if char == "\x18":
                print()
                return "skip"

            # q - Salir del programa
            if char.lower() == "q":
                print()
                return "quit"

            # Ctrl+C
            if char == "\x03":
                print()
                return "cancel"

            # Escape - Saltar resto
            if char == "\x1b":
                print()
                return "skip"
        else:
            import time

            time.sleep(0.01)


def _wait_unix() -> str:
    """Espera tecla en Unix/Linux/macOS."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while True:
            char = sys.stdin.read(1)

            # Ctrl+C
            if char == "\x03":
                raise KeyboardInterrupt

            # Enter
            if char in ("\r", "\n"):
                print()
                return "continue"

            # Ctrl+A - Permitir todos
            if char == "\x01":
                print()
                return "all"

            # Ctrl+X - Saltar resto
            if char == "\x18":
                print()
                return "skip"

            # q - Salir del programa
            if char.lower() == "q":
                print()
                return "quit"

            # Escape - Saltar resto
            if char == "\x1b":
                print()
                return "skip"

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_menu_input(prompt: str = "") -> str:
    """Captura entrada del menú con soporte para teclas especiales.

    Detecta teclas especiales como Supr/Delete para volver atrás.

    Args:
        prompt: Texto a mostrar antes de la entrada

    Returns:
        str: Entrada del usuario o código especial:
            - "-back-" si se presiona Supr/Delete/Backspace
            - "-exit-" si se presiona Ctrl+C
            - "-quit-" si se presiona q (salir del programa)
            - Texto normal en otros casos
    """
    if prompt:
        print(prompt, end="", flush=True)

    try:
        if platform.system() == "Windows":
            return _get_input_windows()
        else:
            return _get_input_unix()
    except KeyboardInterrupt:
        print()
        return "-exit-"


def _get_input_windows() -> str:
    """Captura entrada en Windows con soporte para teclas especiales."""
    chars = []

    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwch()

            # Tecla especial (prefijo 224 o 0)
            if char in ("\x00", "\xe0"):
                special = msvcrt.getwch()
                # Delete = 83, podemos mapear otras teclas aquí
                if special == "S":  # Delete key
                    print()
                    return "-back-"
                continue

            # Backspace
            if char == "\x08":
                if chars:
                    chars.pop()
                    # Borrar caracter en pantalla
                    print("\b \b", end="", flush=True)
                else:
                    # Backspace sin caracteres = volver atrás
                    print()
                    return "-back-"
                continue

            # Enter
            if char in ("\r", "\n"):
                print()
                # Si solo se escribió "q", salir del programa
                if "".join(chars).lower() == "q":
                    return "-quit-"
                return "".join(chars)

            # Escape
            if char == "\x1b":
                print()
                return "-back-"

            # Caracter normal
            print(char, end="", flush=True)
            chars.append(char)
        else:
            # Pequeña pausa para no consumir CPU
            import time

            time.sleep(0.01)


def _get_input_unix() -> str:
    """Captura entrada en Unix/Linux/macOS con soporte para teclas especiales."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chars = []

    try:
        tty.setraw(fd)

        while True:
            char = sys.stdin.read(1)

            # Ctrl+C
            if char == "\x03":
                raise KeyboardInterrupt

            # Escape o secuencia de escape
            if char == "\x1b":
                # Leer más caracteres si es secuencia
                import select

                if select.select([sys.stdin], [], [], 0.1)[0]:
                    seq = sys.stdin.read(2)
                    # Delete = \x1b[3~
                    if seq == "[3":
                        sys.stdin.read(1)  # Leer el ~
                        print()
                        return "-back-"
                else:
                    # Solo Escape
                    print()
                    return "-back-"
                continue

            # Backspace (puede ser \x7f o \x08)
            if char in ("\x7f", "\x08"):
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                else:
                    print()
                    return "-back-"
                continue

            # Enter
            if char in ("\r", "\n"):
                print()
                # Si solo se escribió "q", salir del programa
                if "".join(chars).lower() == "q":
                    return "-quit-"
                return "".join(chars)

            # Caracter normal
            sys.stdout.write(char)
            sys.stdout.flush()
            chars.append(char)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ===========================
# SISTEMA DE MENÚ MODULAR
# ===========================


@dataclass
class MenuItem:
    """Representa una opción de menú.

    Attributes:
        key: Tecla para seleccionar (ej: "1", "2")
        label: Texto descriptivo de la opción
        action: Función a ejecutar al seleccionar
    """

    key: str
    label: str
    action: Callable[[], Optional[bool]]


class Menu:
    """Clase para crear menús interactivos reutilizables.

    Attributes:
        title: Título del menú
        items: Lista de opciones del menú
        show_status: Función opcional para mostrar estado antes del menú
    """

    def __init__(self, title: str, width: int = MENU_WIDTH):
        """Inicializa un nuevo menú.

        Args:
            title: Título del menú
            width: Ancho del encabezado (default: MENU_WIDTH)
        """
        self.title = title
        self.width = width
        self.items: List[MenuItem] = []
        self.show_status: Optional[Callable[[], None]] = None
        self.footer_status: Optional[Callable[[], str]] = None

    def add_item(
        self, key: str, label: str, action: Callable[[], Optional[bool]]
    ) -> "Menu":
        """Añade una opción al menú.

        Args:
            key: Tecla para seleccionar
            label: Texto descriptivo
            action: Función a ejecutar

        Returns:
            Self para encadenamiento
        """
        self.items.append(MenuItem(key=key, label=label, action=action))
        return self

    def set_status_callback(self, callback: Callable[[], None]) -> "Menu":
        """Define una función para mostrar estado antes del menú.

        Args:
            callback: Función que muestra información de estado

        Returns:
            Self para encadenamiento
        """
        self.show_status = callback
        return self

    def set_footer_callback(self, callback: Callable[[], str]) -> "Menu":
        """Define una función para retornar texto dinámico para el footer.

        Args:
            callback: Función que retorna el string a mostrar

        Returns:
            Self para encadenamiento
        """
        self.footer_status = callback
        return self

    def show(self) -> str:
        """Muestra el menú y retorna la opción seleccionada.

        Returns:
            str: Tecla seleccionada por el usuario
        """
        try:
            clear_screen()
            print()
            print(f"{Colors.CYAN}{'═' * self.width}{Colors.RESET}")
            print(f"{Colors.CYAN}{self.title.center(self.width)}{Colors.RESET}")
            print(f"{Colors.CYAN}{'═' * self.width}{Colors.RESET}")
            print()

            # Mostrar estado si hay callback
            if self.show_status:
                self.show_status()
                print()

            # Mostrar opciones
            for item in self.items:
                print(f"{Colors.WHITE}{item.key}. {item.label}{Colors.RESET}")

            # Mostrar ayuda de navegación
            print()
            footer_text = (
                f"{Colors.CYAN}[Supr/Esc: Volver | q+Enter: Salir]{Colors.RESET}"
            )
            if self.footer_status:
                footer_text += f"\n{self.footer_status()}"
            print(footer_text)
            print(f"{Colors.CYAN}{'═' * self.width}{Colors.RESET}")
            print()

            return get_menu_input(f"{Colors.WHITE}Seleccione opción: {Colors.RESET}")
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return "-exit-"

    def run(self, is_main_menu: bool = False) -> bool:
        """Ejecuta el loop principal del menú.

        El loop continúa hasta que una acción retorne True (indicando salir).

        Args:
            is_main_menu: Si True, Esc/Supr cierra el programa en lugar de volver

        Returns:
            bool: True si se solicitó salir del programa (q o Esc en main)

        Teclas especiales:
            - Supr/Delete/Esc: Volver (o salir si es menú principal)
            - q: Salir del programa
            - Ctrl+C: Salir del programa
        """
        try:
            while True:
                choice = self.show()

                # Si el usuario presionó Ctrl+C
                if choice == "-exit-":
                    return True

                # Si el usuario escribió "q" y presionó Enter = salir del programa
                if choice == "-quit-":
                    return "-quit-"

                # Si el usuario presionó Supr/Delete/Esc
                if choice == "-back-":
                    if is_main_menu:
                        # En menú principal, salir del programa
                        print()
                        print(f"{Colors.YELLOW}Saliendo...{Colors.RESET}")
                        return True
                    else:
                        # En submenú, equivale a "0" (volver)
                        choice = "0"

                # Buscar la opción seleccionada
                selected_item = None
                for item in self.items:
                    if item.key == choice:
                        selected_item = item
                        break

                if selected_item:
                    result = selected_item.action()
                    # Si la acción retorna True, salir del menú
                    if result is True:
                        break
                else:
                    print(f"{Colors.RED}Opción inválida{Colors.RESET}")

            return False
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return True
