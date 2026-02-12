# InteractiveGitVersioneer

[![PyPI version](https://img.shields.io/pypi/v/interactive-git-versioneer.svg)](https://pypi.org/project/interactive-git-versioneer/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/amillanaol/interactive-git-versioneer/actions/workflows/auto-tag.yml/badge.svg)](https://github.com/amillanaol/interactive-git-versioneer/actions/workflows/auto-tag.yml)

CLI para gestión de versiones semánticas con IA. Crea tags, genera changelogs y publica releases en GitHub de forma interactiva o automatizada.
## Quick Demo

Aquí se mostrará un GIF animado ilustrando el flujo interactivo de `InteractiveGitVersioneer`.

![Demostración Rápida](https://github.com/amillanaol/interactive-git-versioneer/blob/main/docs/_assets/igv-quick_demo.gif)

Gestor interactivo de versiones Git con soporte para tags, releases de GitHub y generación de mensajes con IA (Groq/OpenAI). Incluye modo CI/CD para pipelines automatizados.

## Características Principales

- **Gestión de Tags**: Menú guiado para crear y gestionar etiquetas de versión
- **Gestión de Releases**: Crear releases en GitHub, generar changelogs
- **Inspección Automática**: Detecta commits sin tag
- **Simulación Segura**: Modos "dry run" para previsualizar cambios
- **Generación con IA**: Integración Groq/OpenAI para mensajes automáticos
- **Arquitectura Modular**: Sistema de menús extensible

## Instalación

### Instalación desde PyPI (Recomendado)

```bash
pip install interactive-git-versioneer
```

### Instalación desde Git

```bash
pip install git+https://github.com/amillanaol/interactive-git-versioneer.git
```

### Instalación desde el Repositorio (Desarrollo)

```bash
git clone https://github.com/amillanaol/interactive-git-versioneer.git
cd interactive-git-versioneer
pip install -e .
```

**Requisitos:** Python >= 3.7

**Opcional:** GitHub CLI (`gh`) para funciones de releases

## Uso Básico

```bash
# Ejecutar menú interactivo principal
igv
```
> Para más comandos consultar el [artículo de comandos disponibles](./docs/comandos-disponibles.md)

**Navegación rápida:** `Supr`/`Esc` para volver, `q` para salir.

## Estructura del Menú

```
GESTOR DE VERSIONES GIT
├── 1. Gestionar Commits
│   ├── Ver lista de commits
│   ├── Procesar commits individualmente
│   ├── Ver preview de tags pendientes
│   ├── Auto-generar todos los tags con IA
│   ├── Aplicar tags
│   └── Volver
├── 2. Gestionar Tags
│   ├── Ver último tag
│   ├── Ver tags locales
│   ├── Ver tags remotos
│   ├── Modificar tag (submenú paginado)
│   ├── Eliminar tag local
│   ├── Eliminar tag remoto
│   ├── Sincronizar con repositorio remoto
│   ├── Generar tags con IA
│   └── Volver al menú principal
├── 3. Gestionar Releases
│   ├── Autenticar con GitHub
│   ├── Crear release en GitHub
│   ├── Generar changelogs
│   ├── Ver releases existentes
│   ├── Modificar un release existente
│   ├── Eliminar un release existente
│   ├── Sincronizar con remoto
│   └── Volver al menú principal
├── 4. Gestionar Changelogs
│   ├── Previsualizar changelog
│   ├── Continuar changelog (manualmente)
│   ├── Continuar changelog (automático con IA)
│   ├── Modificar changelogs
│   ├── Reconstruir todos los changelogs (con IA)
│   └── Volver
├── 5. Configuración
│   ├── Ver configuración actual
│   ├── Configurar IA (Groq/OpenAI)
│   ├── Añadir alias 'igv' al sistema
│   ├── Ayuda - Comandos CLI
│   └── Volver al menú principal
└── 6. Salir
```

## Debugging y Troubleshooting

### Sistema de Logging

Se ha implementado un sistema de logging automático que registra todas las acciones importantes en archivos de log para facilitar el debugging de problemas.

- **Ubicación de logs**: `~/.igv_logs/igv_debug_YYYYMMDD_HHMMSS.log`
- **Activación**: Se activa automáticamente al ejecutar la aplicación
- **Documentación completa**: [LOGGING.md](./LOGGING.md)

El sistema registra:
- Entrada y salida de funciones críticas
- Diálogos mostrados al usuario
- Respuestas del usuario
- Selección de opciones de menú
- Eventos importantes

Útil para debuguear problemas como diálogos duplicados o comportamientos inesperados.

## Documentación Completa

- [Resumen de Documentación](./docs/01-entrada-navegacion/RESUMEN-DOCUMENTACION.md)
- [Mapa Visual de Documentación](./docs/01-entrada-navegacion/MAPA-VISUAL-DOCUMENTACION.md)
- [Changelog Completo](./docs/03-desarrollo/CHANGELOG.md)
- [Documentación de Completitud](./docs/05-referencia/DOCUMENTACION-COMPLETADA.md)
- [Migración de Nomenclatura](./docs/05-referencia/MIGRACION-NOMENCLATURA.md)

### Documentación por Audiencia

- [Guía de Uso - Comandos Básicos](./docs/02-usuario/usuario-inicio-comandos-basicos.md)
- [Integración IA - Configuración Groq](./docs/04-configuracion/configuracion-ia-groq-integracion.md)
- [Referencia - Menú Interactivo](./docs/02-usuario/usuario-referencia-menu-opciones.md)

### Guías de Ejecución

- [Instrucciones de Ejecución Real](./docs/guia-ejecucion-simulacion/instrucciones-ejecucion-real.md)
- [Simulación "Dry Run"](./docs/guia-ejecucion-simulacion/simulacion-dry-run.md)
- [Simulación "Full Dry Run"](./docs/guia-ejecucion-simulacion/simulacion-full-dry-run.md)

### Estrategia de Versionado

- [Plan de Etiquetado de Versiones](./docs/plan-versionado-analisis/plan-etiquetado-versiones.md)
- [Resumen Visual de Versiones](./docs/plan-versionado-analisis/resumen-visual-versiones.md)


---

## 💖 Support My Work

**[ES] Español:**  
¡considera invitarme un café para que pueda seguir creando y compartiendo más! ☕

**[EN] English:**  
Please consider buying me a coffee so I can keep creating and sharing more! ☕

**[BR] Português:**  
Considere me pagar um café para que eu possa continuar criando e compartilhando mais! ☕

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/amillanaol)


## Licencia

Este proyecto se distribuye bajo la Licencia MIT. Consulte el archivo [LICENSE](./LICENSE) para más información.