#!/usr/bin/env bash
# Salir si hay un error
set -o errexit

# Actualizar pip y herramientas de construcción
python -m pip install --upgrade pip setuptools wheel

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones y recolectar estáticos de Django
python manage.py collectstatic --no-input
python manage.py migrate