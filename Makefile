.PHONY: help install install-dev test clean build publish dev lint format

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest

help:
	@echo "Comandos disponibles:"
	@echo "  make install      - Instalar el paquete en modo desarrollo"
	@echo "  make install-dev  - Instalar con dependencias de desarrollo"
	@echo "  make test         - Ejecutar tests con pytest"
	@echo "  make clean        - Limpiar archivos generados"
	@echo "  make build        - Construir el paquete para distribución"
	@echo "  make publish      - Publicar a PyPI (requiere credenciales)"
	@echo "  make dev          - Ejecutar en modo desarrollo"
	@echo "  make lint         - Verificar código con flake8 (si está instalado)"
	@echo "  make format       - Formatear código con black (si está instalado)"

install:
	@echo "Instalando interactive-git-versioneer en modo desarrollo..."
	$(PIP) install -e .
	@echo "Instalación completada. Ejecuta 'igv' para usar la aplicación."

install-dev:
	@echo "Instalando con dependencias de desarrollo..."
	$(PIP) install -e ".[dev]"
	@echo "Instalación completada con dependencias de desarrollo."

test:
	@echo "Ejecutando tests..."
	$(PYTEST) tests/ -v --cov=src/interactive_git_versioneer --cov-report=term-missing

clean:
	@echo "Limpiando archivos generados..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Limpieza completada."

build:
	@echo "Construyendo paquete..."
	$(PYTHON) -m build
	@echo "Paquete construido en dist/"

publish: build
	@echo "Publicando a PyPI..."
	$(PYTHON) -m twine upload dist/*
	@echo "Paquete publicado exitosamente."

dev:
	@echo "Ejecutando igv en modo desarrollo..."
	$(PYTHON) -m interactive_git_versioneer.main

lint:
	@echo "Verificando código con flake8..."
	@which flake8 > /dev/null 2>&1 && flake8 src/ tests/ || echo "flake8 no instalado. Instalar con: pip install flake8"

format:
	@echo "Formateando código con black..."
	@which black > /dev/null 2>&1 && black src/ tests/ || echo "black no instalado. Instalar con: pip install black"
