# Ejecucion de Tests

Documentacion de tests del proyecto.

## Comandos de Ejecucion

| Comando | Alcance | Requisitos |
| :--- | :--- | :--- |
| pytest tests/ | Tests unitarios | Ninguno |
| pytest tests/ -v | Tests con salida verbose | Ninguno |
| pytest tests/ --cov=src | Cobertura completa | pytest-cov instalado |

## Descripcion de Tests

El proyecto incluye tests unitarios en el directorio `tests/` que cubren los modulos principales:

- **test_config.py**: Tests para el modulo de configuracion (carga, guardado, validacion)
- **test_models.py**: Tests para los modelos de datos (Commit, Version)
- **test_git_ops.py**: Tests para operaciones Git (get_last_tag, get_next_version, get_untagged_commits)
- **test_clean_duplicates.py**: Tests para limpieza de duplicados

## Configuracion

Los tests utilizan pytest. Para ejecutar:

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# o instalar pytest directamente
pip install pytest

# Ejecutar todos los tests
pytest tests/

# Con coverage
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

## Control de versiones

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | En desarrollo |
| **Ultima Actualizacion** | 2026-04-22 |