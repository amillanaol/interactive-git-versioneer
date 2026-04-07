#!/usr/bin/env python3
"""Menu interactivo para instalar/desinstalar el modulo IGV."""

import os
import subprocess
import sys
from pathlib import Path


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    clear_screen()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        INTERACTIVE GIT VERSIONEER - INSTALACION          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def print_option(number, title, description):
    print(f"  {number}. {title}")
    print(f"      {description}")
    print()


def get_python_installations():
    """Busca instalaciones de Python en el sistema."""
    pythons = []

    if os.name == "nt":
        local_programs = (
            Path(os.environ.get("LocalAppData", "")) / "Programs" / "Python"
        )

        if local_programs.exists():
            for python_dir in local_programs.glob("Python*"):
                if python_dir.is_dir():
                    pip_exe = python_dir / "Scripts" / "pip.exe"
                    python_exe = python_dir / "python.exe"
                    if pip_exe.exists():
                        pythons.append(
                            {
                                "path": str(pip_exe),
                                "version": python_dir.name.replace("Python", ""),
                                "python": str(python_exe),
                                "scripts": str(python_dir / "Scripts"),
                            }
                        )

    return pythons


def find_package_location():
    """Busca donde esta instalado el paquete en todas las instalaciones de Python."""
    pythons = get_python_installations()

    for py_info in pythons:
        result = subprocess.run(
            [py_info["path"], "show", "interactive-git-versioneer"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return py_info

    return None


def add_to_path(scripts_path):
    """Agrega el directorio Scripts al PATH del usuario en el perfil de PowerShell."""
    if os.name != "nt":
        return True, "Solo soportado en Windows"

    current_path = os.environ.get("PATH", "")

    if scripts_path in current_path:
        return True, "Ya esta en PATH"

    try:
        profile_path = (
            Path.home()
            / "Documents"
            / "WindowsPowerShell"
            / "Microsoft.PowerShell_profile.ps1"
        )
        if not profile_path.exists():
            profile_path = (
                Path.home()
                / "Documents"
                / "PowerShell"
                / "Microsoft.PowerShell_profile.ps1"
            )

        path_line = f'$env:PATH += ";{scripts_path}"'

        if profile_path.exists():
            content = profile_path.read_text(encoding="utf-8")
            if path_line not in content:
                with open(profile_path, "a", encoding="utf-8") as f:
                    f.write(f"\n# IGV - Python Scripts PATH\n{path_line}\n")
                return (
                    True,
                    f"Agregado a: {profile_path}\nReinicia tu terminal para aplicar cambios.",
                )
            else:
                return True, "Ya esta en el perfil de PowerShell"
        else:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(f"# IGV - Python Scripts PATH\n{path_line}\n")
            return (
                True,
                f"Creado perfil: {profile_path}\nReinicia tu terminal para aplicar cambios.",
            )
    except Exception as e:
        return False, f"Error al agregar al PATH: {e}"


def run_menu():
    while True:
        print_header()
        print("Que desea hacer?\n")
        print_option(
            "1", "Instalar", "Instala el modulo en modo editable (recomendado)"
        )
        print_option("2", "Desinstalar", "Desinstala el modulo del sistema")
        print_option(
            "3", "Reinstalar", "Desinstala y reinstalla el modulo sin preguntar"
        )
        print_option("0", "Salir", "Cancelar y salir\n")

        try:
            choice = input("Seleccione opcion: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nOperacion cancelada.")
            sys.exit(0)

        if choice == "1":
            install()
        elif choice == "2":
            uninstall()
        elif choice == "3":
            reinstall()
        elif choice == "0":
            print("\nHasta luego!")
            sys.exit(0)
        else:
            print("\nOpcion invalida. Presione Enter para continuar...")
            try:
                input()
            except (KeyboardInterrupt, EOFError):
                pass


def is_installed():
    """Verifica si el paquete esta instalado."""
    return find_package_location() is not None


def get_pip_path():
    """Obtiene el path de pip y scripts, buscando en el Python actual primero."""
    scripts_dir = str(Path(sys.executable).parent / "Scripts")
    current_pip = Path(sys.executable).parent / "Scripts" / "pip.exe"

    if current_pip.exists():
        return {
            "pip": str(current_pip),
            "scripts": scripts_dir,
            "version": Path(sys.executable).parent.name.replace("Python", ""),
        }

    pythons = get_python_installations()
    if pythons:
        return {
            "path": pythons[0]["path"],
            "scripts": pythons[0]["scripts"],
            "version": pythons[0]["version"],
        }

    return None


def install():
    print_header()
    print("INSTALANDO EN MODO EDITABLE...\n")

    location = find_package_location()
    if location:
        print(f"El modulo ya esta instalado en Python {location['version']}.")
        print("Primero debe desinstalarlo para reinstalarlo.")
        print()
        try:
            input("Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    pip_info = get_pip_path()
    if not pip_info:
        print("No se encontro una instalacion de Python valida.")
        print()
        try:
            input("Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    pip_path = pip_info["path"] if "path" in pip_info else pip_info["pip"]
    scripts_path = pip_info["scripts"]

    print(f"Usando pip: {pip_path}")
    print(f"Scripts: {scripts_path}\n")

    try:
        result = subprocess.run(
            [pip_path, "install", "-e", "."],
            check=False,
        )
        if result.returncode == 0:
            print("Instalacion completada exitosamente.\n")

            success, message = add_to_path(scripts_path)
            if success:
                print(f"[OK] {message}")
            else:
                print(f"[!] {message}")
                print("    Agrega manualmente al PATH si es necesario.")

            print()
            print("Ahora puedes usar el comando 'igv' desde cualquier directorio.")
            print("Ejecuta 'igv --help' para ver las opciones disponibles.")
            print("\nSi 'igv' no funciona, reinicia tu terminal.")
        else:
            print(f"\nError durante la instalacion (codigo: {result.returncode})\n")
            stdout = result.stdout.decode() if result.stdout else ""
            stderr = result.stderr.decode() if result.stderr else ""
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
    except Exception as e:
        print(f"\nError inesperado: {e}\n")

    try:
        input("\nPresione Enter para continuar...")
    except (KeyboardInterrupt, EOFError):
        pass


def uninstall():
    print_header()
    print("DESINSTALANDO MODULO...\n")

    location = find_package_location()

    if not location:
        print("El modulo no esta instalado.\n")
        try:
            input("Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    print(f"Paquete encontrado en Python {location['version']}.")
    print(f"Ubicacion: {location['path']}\n")

    print("Esta seguro de que desea desinstalar?")
    try:
        confirm = input("(s/n): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperacion cancelada.")
        sys.exit(0)

    if confirm != "s":
        print("\nOperacion cancelada.\n")
        try:
            input("Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    try:
        result = subprocess.run(
            [location["path"], "uninstall", "-y", "interactive-git-versioneer"],
            check=False,
        )
        if result.returncode == 0:
            print("\nDesinstalacion completada.\n")
        else:
            print(f"\nError durante la desinstalacion (codigo: {result.returncode})\n")
            stdout = result.stdout.decode() if result.stdout else ""
            stderr = result.stderr.decode() if result.stderr else ""
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
    except Exception as e:
        print(f"\nError inesperado: {e}\n")

    try:
        input("Presione Enter para continuar...")
    except (KeyboardInterrupt, EOFError):
        pass


def reinstall():
    """Reinstala el modulo sin preguntar."""
    print_header()
    print("REINSTALANDO MODULO...\n")

    location = find_package_location()
    if location:
        print(f"Desinstalando version anterior en Python {location['version']}...")
        try:
            subprocess.run(
                [location["path"], "uninstall", "-y", "interactive-git-versioneer"],
                check=False,
            )
        except Exception:
            pass

    pip_info = get_pip_path()
    if not pip_info:
        print("No se encontro una instalacion de Python valida.")
        try:
            input("Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    pip_path = pip_info["path"] if "path" in pip_info else pip_info["pip"]
    scripts_path = pip_info["scripts"]

    print(f"Usando pip: {pip_path}")
    print(f"Scripts: {scripts_path}\n")

    try:
        result = subprocess.run(
            [pip_path, "install", "-e", "."],
            check=False,
        )
        if result.returncode == 0:
            print("Reinstalacion completada exitosamente.\n")

            success, message = add_to_path(scripts_path)
            if success:
                print(f"[OK] {message}")
            else:
                print(f"[!] {message}")

            print()
            print("Ahora puedes usar el comando 'igv' desde cualquier directorio.")
            print("Ejecuta 'igv --help' para ver las opciones disponibles.")
        else:
            print(f"\nError durante la reinstalacion (codigo: {result.returncode})\n")
    except Exception as e:
        print(f"\nError inesperado: {e}\n")

    try:
        input("\nPresione Enter para continuar...")
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    try:
        run_menu()
    except KeyboardInterrupt:
        print("\n\nHasta luego!")
        sys.exit(0)
