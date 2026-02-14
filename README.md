# Interactive Git Versioneer

Interfaz CLI que combina menús interactivos con modelos de IA para automatizar el versionado semántico, generación de changelogs y releases en Git.

| | | |
| :---: | :---: | :---: |
| ![PyPI](https://img.shields.io/pypi/v/interactive-git-versioneer.svg?label=Version) | ![License](https://img.shields.io/badge/license-MIT-blue?label=License) | ![Python](https://img.shields.io/badge/python-3.7+-blue?label=Python) |
| ![Downloads](https://img.shields.io/pypi/dm/interactive-git-versioneer?label=Downloads) | ![Build](https://github.com/amillanaol/interactive-git-versioneer/actions/workflows/auto-tag.yml/badge.svg?label=Build) | ![GitHub stars](https://img.shields.io/github/stars/amillanaol/interactive-git-versioneer?label=Stars) |

## Inicio Rápido

| Necesidad | Comando |
| :--- | :--- |
| Instalar | `pip install interactive-git-versioneer` |
| Ejecutar menú | `igv` |
| Etiquetado automático CI/CD | `igv tag --auto --push` |
| Configurar IA | `igv config set OPENAI.key <key>` |

[Guía de inicio rápido](docs/usuario/guia_inicio_rapido.md) | [Comandos CLI](docs/referencia/comandos.md)

## Demostración

Demostración del menú interactivo: navegación por menús, selección de commits, generación automática de mensajes con IA y aplicación de tags con versionado semántico.

![](https://raw.githubusercontent.com/amillanaol/interactive-git-versioneer/refs/heads/main/docs/_assets/igv-quick_demo.gif)

## Instalación

| Método | Comando | Requisitos |
| :--- | :--- | :--- |
| PyPI (recomendado) | `pip install interactive-git-versioneer` | Python >= 3.7 |
| Desde Git | `pip install git+https://github.com/amillanaol/interactive-git-versioneer.git` | Git |
| Desarrollo | `git clone` + `pip install -e .` | Python >= 3.7, Git |

**Dependencias:** `GitPython>=3.1.0`, `openai>=1.0.0`
**Opcional:** `gh` (GitHub CLI) para releases.

## Desarrollo y Build

### Comandos Make Disponibles

El proyecto incluye un `Makefile` para automatizar tareas comunes de desarrollo:

| Comando | Descripción |
| :--- | :--- |
| `make help` | Muestra todos los comandos disponibles |
| `make clean` | Limpia archivos de build (dist/, build/, *.egg-info) |
| `make build` | Limpia y construye el paquete |
| `make upload-test` | Sube el paquete a TestPyPI |
| `make upload` | Sube el paquete a PyPI (producción) |
| `make install` | Instala localmente en modo editable |
| `make dev` | Instala dependencias de desarrollo |
| `make test` | Ejecuta tests con pytest |

### Flujo de Publicación

**Para TestPyPI (testing):**
```bash
cd interactive-git-versioneer
make build        # Limpia y construye con la versión en pyproject.toml
make upload-test  # Sube a TestPyPI
```

**Para PyPI (producción):**
```bash
# 1. Actualizar versión en pyproject.toml
# 2. Crear tag git: git tag v3.1.6 && git push --tags
make upload       # Construye y sube a PyPI (con confirmación)
```

**Notas importantes:**
- PyPI/TestPyPI **NO permiten reutilizar versiones**. Si `v3.1.6` ya existe, debes incrementar a `v3.1.7`
- `make build` automáticamente limpia archivos viejos antes de construir
- Configura tokens en `~/.pypirc` ([ver configuración](docs/operaciones/publicacion_pypi.md))

## Documentación

| Sección | Ubicación |
| :--- | :--- |
| Guía de inicio | [docs/usuario/guia_inicio_rapido.md](docs/usuario/guia_inicio_rapido.md) |
| Comandos CLI | [docs/referencia/comandos.md](docs/referencia/comandos.md) |
| Configuración IA | [docs/referencia/configuracion_ia.md](docs/referencia/configuracion_ia.md) |
| Modelos de datos | [docs/modules/modelos.md](docs/modules/modelos.md) |
| Resolución errores | [docs/operaciones/resolucion_errores.md](docs/operaciones/resolucion_errores.md) |
| Módulos | [docs/modules/](docs/modules/) |
| Referencia API | [docs/referencia/api_documentacion.md](docs/referencia/api_documentacion.md) |

## Estructura de Módulos

| Módulo | Responsabilidad |
| :--- | :--- |
| **Core** (`core/`) | Operaciones base: Git, versiones, IA |
| **Tags** (`tags/`) | Gestión de etiquetas y menús interactivos |
| **Releases** (`releases/`) | Releases GitHub y changelogs |
| **Config** (`config/`) | Configuración del sistema |

Detalles en [docs/modules/](docs/modules/).

---

## Support

| | |
| :---: | :---: |
| [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&label=Support)](https://buymeacoffee.com/amillanaol) | [![GitHub Stars](https://img.shields.io/badge/GitHub-Stars-181717?style=for-the-badge&logo=github&label=Star)](https://github.com/amillanaol/interactive-git-versioneer/stargazers) |
