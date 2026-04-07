.PHONY: help clean build install uninstall reinstall dev test

help:
	@echo "Comandos disponibles para Interactive Git Versioneer:"
	@echo ""
	@echo "  make clean        - Limpia archivos de build (dist/, build/, *.egg-info)"
	@echo "  make build        - Limpia y construye el paquete"
	@echo "  make install      - Menu interactivo: Instalar o Desinstalar"
	@echo "  make reinstall    - Reinstalar sin preguntar (sobrescribe instalación existente)"
	@echo "  make uninstall    - Desinstala el modulo directamente"
	@echo "  make dev          - Instala dependencias de desarrollo"
	@echo "  make test         - Ejecuta los tests con pytest"
	@echo ""

clean:
	@echo "Limpiando archivos de build..."
	rm -rf dist/
	rm -rf build/
	rm -rf src/*.egg-info
	rm -rf *.egg-info
	@echo "Limpieza completada"

build: clean
	@echo "Construyendo el paquete..."
	python -m build
	@echo "Build completado. Archivos en dist/:"
	@ls -lh dist/

install:
	python scripts/install_menu.py

reinstall:
	@echo "Reinstalando modulo..."
	pip uninstall -y interactive-git-versioneer || true
	pip install -e .
	@echo "Reinstalación completada"

uninstall:
	@echo "Desinstalando modulo..."
	pip uninstall -y interactive-git-versioneer

dev:
	@echo "Instalando dependencias de desarrollo..."
	pip install -e ".[dev]"
	pip install build twine

test:
	@echo "Ejecutando tests..."
	pytest tests/ -v
