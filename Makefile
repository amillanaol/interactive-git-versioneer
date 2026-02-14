.PHONY: help clean build upload-test upload install dev test

help:
	@echo "Comandos disponibles para Interactive Git Versioneer:"
	@echo ""
	@echo "  make clean        - Limpia archivos de build (dist/, build/, *.egg-info)"
	@echo "  make build        - Limpia y construye el paquete"
	@echo "  make upload-test  - Sube el paquete a TestPyPI"
	@echo "  make upload       - Sube el paquete a PyPI (producción)"
	@echo "  make install      - Instala el paquete localmente en modo editable"
	@echo "  make dev          - Instala dependencias de desarrollo"
	@echo "  make test         - Ejecuta los tests con pytest"
	@echo ""

clean:
	@echo "🧹 Limpiando archivos de build..."
	rm -rf dist/
	rm -rf build/
	rm -rf src/*.egg-info
	rm -rf *.egg-info
	@echo "✅ Limpieza completada"

build: clean
	@echo "🔨 Construyendo el paquete..."
	python -m build
	@echo "✅ Build completado. Archivos en dist/:"
	@ls -lh dist/

upload-test: build
	@echo "📤 Subiendo a TestPyPI..."
	python -m twine upload --repository testpypi dist/* --verbose

upload: build
	@echo "⚠️  ADVERTENCIA: Vas a subir a PyPI PRODUCCIÓN"
	@echo "Presiona Ctrl+C para cancelar, Enter para continuar..."
	@read dummy
	python -m twine upload dist/* --verbose

install:
	@echo "📦 Instalando en modo editable..."
	pip install -e .

dev:
	@echo "🛠️  Instalando dependencias de desarrollo..."
	pip install -e ".[dev]"
	pip install build twine

test:
	@echo "🧪 Ejecutando tests..."
	pytest tests/ -v
