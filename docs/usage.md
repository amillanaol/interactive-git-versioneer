# Uso rápido

## Instalación

1. Clona el repositorio
2. Instala el paquete en editable (recomendado para desarrollo):

```bash
pip install -e .
```

## Comandos principales

- `igv` — interfaz principal (menú interactivo)
- `igv tag` — subcomandos de tagging (si están expuestos)

## Configuración de IA (opcional)

Configura las claves con `igv config set`:

- `OPENAI.key` — API key
- `OPENAI.baseURL` — URL base del proveedor

## Generar documentación

Instala MkDocs y mkdocstrings y ejecuta:

```bash
pip install mkdocs mkdocstrings[python]
mkdocs build
```
