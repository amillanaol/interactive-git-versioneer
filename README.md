# Interactive Git Versioneer

Interfaz CLI que combina menús interactivos con modelos de IA para automatizar el versionado semántico, generación de changelogs y releases en Git.

## Demostración

Demostración del menú interactivo: navegación por menús, selección de commits, generación automática de mensajes con IA y aplicación de tags con versionado semántico.

![](https://raw.githubusercontent.com/amillanaol/interactive-git-versioneer/refs/heads/main/docs/_assets/igv-quick_demo.gif)

## Inicio Rápido

| Necesidad | Comando |
| :--- | :--- |
| Instalar | `pip install interactive-git-versioneer` |
| Ejecutar menú | `igv` |
| Etiquetado automático CI/CD | `igv tag --auto --push` |
| Configurar IA | `igv config set OPENAI.key <key>` |

[Guía de inicio rápido](docs/usuario/guia_inicio_rapido.md) | [Comandos CLI](docs/referencia/comandos.md)

## Instalación

| Método | Comando | Requisitos |
| :--- | :--- | :--- |
| PyPI (recomendado) | `pip install interactive-git-versioneer` | Python >= 3.7 |
| Desde Git | `pip install git+https://github.com/amillanaol/interactive-git-versioneer.git` | Git |
| Desarrollo | `git clone` + `pip install -e .` | Python >= 3.7, Git |

**Dependencias:** `GitPython>=3.1.0`, `openai>=1.0.0`  
**Opcional:** `gh` (GitHub CLI) para releases.

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

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |

## 💖 Support My Work

**[ES] Español:**  
¡considera invitarme un café para que pueda seguir creando y compartiendo más! ☕

**[EN] English:**  
Please consider buying me a coffee so I can keep creating and sharing more! ☕

**[BR] Português:**  
Considere me pagar um café para que eu possa continuar criando e compartilhando mais! ☕

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/amillanaol)
