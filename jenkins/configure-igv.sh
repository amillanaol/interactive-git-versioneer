#!/bin/bash
# =============================================================================
# Script de configuración post-despliegue para igv
# Credenciales de API (Groq/OpenAI)
# =============================================================================

set -e

VENV_DIR="/opt/igv/venv"

# Activar entorno virtual
source "${VENV_DIR}/bin/activate"

# Configurar Groq API (las variables vienen de Jenkins credentials)
if [ -n "${GROQ_API_KEY}" ]; then
    echo "Configurando Groq API..."
    igv config set OPENAI.key "${GROQ_API_KEY}"
    igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"
    igv config set OPENAI.model "llama-3.3-70b-versatile"
    echo "Configuración de API completada"
else
    echo "ADVERTENCIA: GROQ_API_KEY no está definida"
fi

# Mostrar configuración actual (sin mostrar la key completa)
echo ""
echo "Configuración actual:"
igv config list

deactivate
