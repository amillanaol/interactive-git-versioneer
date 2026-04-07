"""Interactive Git Versioneer - Gestor interactivo de versiones Git."""

import sys
from pathlib import Path

__app_name__ = "igv"
__package_name__ = "interactive-git-versioneer"

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    # Python < 3.8
    from importlib_metadata import PackageNotFoundError, version


def _get_version() -> str:
    """Retrieves the package version from pyproject.toml."""
    import tomli

    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                return tomli.load(f)["project"]["version"]
    except Exception:
        pass
    return "1.0.0"


__version__ = _get_version()

__all__ = ["__app_name__", "__package_name__", "__version__"]
