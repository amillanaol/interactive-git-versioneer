#!/bin/bash
# =============================================================================
# Script de despliegue para Interactive Git Versioneer
# Este script es ejecutado por Jenkins para instalar/actualizar igv
# =============================================================================

set -e  # Salir inmediatamente si un comando falla

# Configuración
INSTALL_DIR="/opt/igv"
VENV_DIR="${INSTALL_DIR}/venv"
LOG_FILE="/var/log/igv-deploy.log"

echo "=========================================="
echo "Despliegue de Interactive Git Versioneer"
echo "Fecha: $(date)"
echo "=========================================="

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Crear directorio de instalación si no existe
sudo mkdir -p "${INSTALL_DIR}"
sudo chown -R jenkins:jenkins "${INSTALL_DIR}"

# Crear o actualizar el entorno virtual
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "${VENV_DIR}"
fi

# Activar entorno virtual
source "${VENV_DIR}/bin/activate"

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar/actualizar el paquete desde el workspace de Jenkins
echo "Instalando Interactive Git Versioneer..."
pip install --upgrade .

# Verificar instalación
echo "Verificando instalación..."
igv --version || echo "Instalación completada (sin flag --version)"

# Crear enlace simbólico global (opcional)
if [ ! -L "/usr/local/bin/igv" ]; then
    echo "Creando enlace simbólico en /usr/local/bin/igv..."
    sudo ln -sf "${VENV_DIR}/bin/igv" /usr/local/bin/igv
fi

# Mostrar información de la instalación
echo ""
echo "=========================================="
echo "Despliegue completado exitosamente"
echo "Ejecutable: ${VENV_DIR}/bin/igv"
echo "Enlace global: /usr/local/bin/igv"
echo "=========================================="

# Desactivar entorno virtual
deactivate
