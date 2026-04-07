# Interactive Git Versioneer con IA

Interactive Git Versioneer es una herramienta open-source que automatiza flujos de versionado en Git mediante un adaptador único basado en OpenAI. Combina comandos interactivos en Node.js con modelos de IA para generar tags semánticos, changelogs inteligentes y merges optimizados, ideal para equipos DevOps. Desarrollado con Clean Architecture, soporta CI/CD y microservicios. ¡Prueba la demo y contribuye!

<!-- Badges mostly generated with https://shields.io -->

[![Build](https://github.com/amillanaol/interactive-git-versioneer/actions/workflows/auto-tag.yml/badge.svg?label=Build)](https://github.com/amillanaol/interactive-git-versioneer/actions?query=workflow:"Build")
[![License](https://img.shields.io/badge/License-MIT-blue)](#license "Go to License section")
[![PyPI](https://img.shields.io/pypi/v/interactive-git-versioneer.svg?label=Version)](https://pypi.org/project/interactive-git-versioneer/)
[![Contributions - welcome](https://img.shields.io/badge/contributions-welcome-blue)](/CONTRIBUTING.md "View contributing doc")

<div align="center">

<!-- Logo placeholder - replace with actual image URL -->
<a href="https://github.com/amillanaol/interactive-git-versioneer"
    title="Interactive Git Versioneer">

![maintained - yes](https://img.shields.io/badge/maintained-yes-blue)

</a>

**[Getting started](#getting-started) | [Features](#features) | [Documentation](#documentation)**

</div>

## Preview

Demostracion del menu interactivo: navegacion por menus, seleccion de commits, generacion automatica de mensajes con IA y aplicacion de tags con versionado semantico.

<div align="center">
    <img src="https://raw.githubusercontent.com/amillanaol/interactive-git-versioneer/refs/heads/main/docs/_assets/igv-quick_demo.gif"
        alt="IGV Demo"
        width="700" />
</div>


## Getting started

<div align="center">

[![docs - Getting started](https://img.shields.io/badge/docs-getting_started-2ea44f?style=for-the-badge)](/docs/usuario/guia_inicio_rapido.md)

<div align="center">
    <img src="https://raw.githubusercontent.com/amillanaol/interactive-git-versioneer/refs/heads/main/docs/_assets/igv-ia-diagram.png"
        alt="IGV "
        width="700" />
</div>

</div>


## Features

- Menu interactivo para gestion de commits y tags
- Generacion automatica de tags con IA (Groq, OpenAI, Ollama, OpenRouter)
- Versionado semantico (major/minor/patch)
- Generacion de changelogs automaticamente
- Releases en GitHub con CLI
- Modo CI/CD para pipelines automatizados
- Configuracion de multiples proveedores de IA

See more info on the [Features](/docs/modules/tagger.md) page in the docs.


## Indice de la documentacion

| Necesidad | Ubicacion |
| :--- | :--- |
| Instalar y ejecutar localmente | [docs/usuario/guia_inicio_rapido.md](docs/usuario/guia_inicio_rapido.md) |
| Configurar proveedores de IA | [docs/referencia/configuracion_ia.md](docs/referencia/configuracion_ia.md) |
| Modelos Ollama recomendados | [docs/configuracion/modelos_ollama.md](docs/configuracion/modelos_ollama.md) |
| Referencia de comandos CLI | [docs/referencia/comandos.md](docs/referencia/comandos.md) |
| Resolucion de errores comunes | [docs/operaciones/resolucion_errores.md](docs/operaciones/resolucion_errores.md) |
| Arquitectura del modulo | [docs/modules/modelos.md](docs/modules/modelos.md) |
| Modulo de tags | [docs/modules/tagger.md](docs/modules/tagger.md) |
| Releases y changelogs | [docs/modules/releases.md](docs/modules/releases.md) |
| Integracion CI/CD | [docs/operaciones/cicd_diagnostico.md](docs/operaciones/cicd_diagnostico.md) |

## Stack Tecnico del proyecto

| Componente | Tecnologia | Version |
| :--- | :--- | :--- |
| Lenguaje | Python | >=3.7 |
| Dependencias | GitPython, openai | 3.1+, 1.0+ |
| Opcional | GitHub CLI (gh) | latest |
| Linter | Ruff | 0.8+ |

## Estructura del Proyecto

```
src/interactive_git_versioneer/
  core/           # Operaciones base: Git, versiones, IA
    git_ops.py    # get_last_tag, get_next_version, get_untagged_commits
    ai.py         # Integracion OpenAI-compatible
    ui.py         # Sistema de menus y UI
    models.py     # Modelos de datos (Commit)
  tags/           # Gestion de etiquetas
    tagger.py     # Menu principal de tags
    menus.py      # Submenus interactivos
    actions.py    # apply_tags, clean_all_tags
    ai.py         # auto_generate_all_with_ai
  releases/       # Releases GitHub y changelogs
    menus.py
    changelog_actions.py
    gh_releases.py
  config/         # Configuracion ~/.igv/config.json
    config.py
    menu.py
  tui/            # Terminal UI (Textual)
scripts/
  install_menu.py # Menu interactivo de instalacion
```

> **Nota sobre tests:** Los tests unitarios y de integracion estan en un repositorio privado por ahora. Para tener acceso, contactar a alexis.millanao@protonmail.com

## Inicio Rapido

```bash
# 1. Instalar el paquete
pip install interactive-git-versioneer

# 2. O instalar desde el codigo fuente con menu interactivo
make install

# 3. Configurar la clave de API (opcional - requerido para IA)
igv config set OPENAI.key "tu_api_key"
igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"

# 4. Ejecutar el menu interactivo
igv

# 5. O ejecutar en modo automatico (CI/CD)
igv tag --auto --push
```

## Comandos Make Disponibles

| Comando | Descripcion |
| :--- | :--- |
| `make help` | Muestra todos los comandos disponibles |
| `make clean` | Limpia archivos de build (dist/, build/, *.egg-info) |
| `make build` | Limpia y construye el paquete |
| `make install` | Menu interactivo: Instalar o Desinstalar |
| `make dev` | Instala dependencias de desarrollo |

## Tests

> **Nota:** Los tests unitarios y de integracion se han trasladados a un **repositorio privado**. Si necesitas acceso a la suite de pruebas para auditoria o desarrollo, por favor solicita acceso enviando un correo a: **alexis.millanao@protonmail.com**

## Resolucion de Errores

| Sintoma | Causa Raiz | Solucion Tecnica |
| :--- | :--- | :--- |
| `Error: Not a valid Git repository` | Directorio actual no es repo Git | Ejecutar `igv` desde directorio con `.git/` |
| `ModuleNotFoundError: No module named 'interactive_git_versioneer'` | Paquete no instalado | Ejecutar `pip install -e .` o `make install` |
| `API key not configured` | Falta `OPENAI.key` en config | `igv config set OPENAI.key "<tu_api_key>"` |
| `Base URL not configured` | Falta `OPENAI.baseURL` en config | `igv config set OPENAI.baseURL "<url_proveedor>"` |
| `Invalid or unconfigured API Key` | API key invalida o expirada | Verificar key en el panel del proveedor |
| `GitHub CLI is not installed` | Falta `gh` en PATH | Instalar desde https://cli.github.com/ |
| `Not authenticated` | `gh` sin autenticacion | Ejecutar `gh auth login` |
| No se muestran commits | HEAD coincide con ultimo tag | Crear nuevos commits antes de etiquetar |

**NOTA:** Para lista completa de errores, ver [docs/operaciones/resolucion_errores.md](docs/operaciones/resolucion_errores.md).

## Contributing

See the [Contributing](/CONTRIBUTING.md) guide.


## License

Released under [MIT](/LICENSE) by [@amillanaol](https://github.com/amillanaol).

## Control de versiones

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | En desarrollo |
| **Ultima Actualizacion** | 2026-03-25 |
