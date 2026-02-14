| Necesidad | Ubicación |
| :--- | :--- |
| Instalar en modo desarrollo | `pip install -e .` |
| Ejecutar interfaz principal | `igv` |
| Configurar API key | `igv config set OPENAI.key <key>` |
| Configurar base URL | `igv config set OPENAI.baseURL <url>` |

## Instalación

| Método | Comando | Contexto |
| :--- | :--- | :--- |
| Desarrollo | `pip install -e .` | Desde directorio del proyecto |
| Producción | `pip install interactive-git-versioneer` | PyPI |

## Comandos Principales

| Comando | Descripción |
| :--- | :--- |
| `igv` | Interfaz principal con menú interactivo |
| `igv tag` | Subcomandos de etiquetado |
| `igv tag --auto` | Modo automático CI/CD |
| `igv tag --dry-run` | Simulación sin cambios |

## Configuración de IA

Claves: `OPENAI.key`, `OPENAI.baseURL`.

Ejemplo:
```bash
igv config set OPENAI.key "gsk_your_key"
igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"
```

## Generación de Documentación

Dependencias: `mkdocs`, `mkdocstrings[python]`.

| Comando | Acción |
| :--- | :--- |
| `mkdocs build` | Generar documentación estática |
| `mkdocs serve` | Servir documentación localmente |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
