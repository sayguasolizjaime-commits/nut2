#!/bin/bash
# ================================================================
# NutriClinic — Sistema Nutricional Profesional
# Script de inicio para Linux
# ================================================================

cd "$(dirname "$0")"

echo "========================================"
echo "  NutriClinic — Sistema Nutricional"
echo "========================================"

# Verificar Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado."
    echo "Instálalo con: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo ""
    echo "Creando entorno virtual por primera vez..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado."
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar/verificar dependencias
echo "Verificando dependencias..."
pip install streamlit pandas openpyxl python-dateutil xlrd --quiet --upgrade

echo ""
echo "✅ Todo listo. Iniciando NutriClinic..."
echo "Abre tu navegador en: http://localhost:8501"
echo "Para detener: Ctrl+C"
echo "========================================"
echo ""

# Usar python -m streamlit para garantizar que use el venv correcto
python3 -m streamlit run app.py
