import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from matplotlib.figure import Figure
from datetime import datetime

# Configuración estética de Seaborn
sns.set_theme(style="whitegrid")

# --- 1. FUNCIONES DE LLAMADA A API (GEOPOSICIONAMIENTO Y CLIMA) ---

def obtener_coordenadas(estado, pais):
    """
    Busca coordenadas basadas en el Estado y País con Headers para evitar bloqueos en Render.
    """
    busqueda = f"{estado.strip()}, {pais.strip()}".replace(" ", "+")
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={busqueda}&count=1&language=es&format=json"
    
    # User-Agent necesario para que la API no bloquee la IP del servidor de Render
    headers = {'User-Agent': 'MeteoAnalytics/1.0 (contact@example.com)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if "results" in data:
            result = data["results"][0]
            # Retornamos lat, lon y el nombre oficial (Estado)
            return result["latitude"], result["longitude"], result.get("name", estado)
        return None, None, None
    except Exception as e:
        print(f"Error en Geocoding: {e}")
        return None, None, None

def obtener_datos_meteorologicos(estado, pais, anio):
    """
    Obtiene los datos climáticos históricos.
    """
    lat, lon, nombre_oficial = obtener_coordenadas(estado, pais)
    
    if lat is None:
        return pd.DataFrame()

    headers = {'User-Agent': 'MeteoAnalytics/1.0 (contact@example.com)'}
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={anio}-01-01&end_date={anio}-12-31&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        if 'daily' not in data:
            print(f"API Error en {nombre_oficial}: {data}")
            return pd.DataFrame()

        df = pd.DataFrame({
            'Fecha': pd.to_datetime(data['daily']['time']),
            'Temperatura Maxima': data['daily']['temperature_2m_max'],
            'Temperatura Minima': data['daily']['temperature_2m_min'],
            'Ubicacion': nombre_oficial.capitalize()
        })
        
        meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                    7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
        
        df['Mes'] = df['Fecha'].dt.month.map(meses_es)
        df['Dia'] = df['Fecha'].dt.day
        return df
    except Exception as e:
        print(f"Error al obtener clima: {e}")
        return pd.DataFrame()

# --- 2. FUNCIONES DE CÁLCULO ESTADÍSTICO ---

def obtener_resumen_estadistico(df, mes=None):
    """Calcula KPIs basados en el DataFrame."""
    if df.empty: return None
    
    df_filtrado = df.copy()
    if mes and mes.strip():
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes.capitalize()]
    
    if df_filtrado.empty: return None

    return {
        'max_abs': df_filtrado['Temperatura Maxima'].max(),
        'min_abs': df_filtrado['Temperatura Minima'].min(),
        'promedio': round(df_filtrado['Temperatura Maxima'].mean(), 1),
    }

# --- 3. FUNCIONES DE GENERACIÓN DE GRÁFICOS ---

def fig_to_base64(fig):
    """Convierte un objeto Figure a cadena Base64 para HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_grafico_individual(df, mes):
    """Gráfico de barras para un mes específico."""
    df_mes = df[df['Mes'] == mes.capitalize()]
    if df_mes.empty: return None

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.barplot(data=df_mes, x='Dia', y='Temperatura Maxima', ax=ax, palette='Oranges')
    ax.set_title(f"Temperaturas Máximas en {mes} ({df_mes['Ubicacion'].iloc[0]})", fontsize=14, fontweight='bold')
    ax.set_xlabel("Día del Mes")
    ax.set_ylabel("Temperatura (°C)")
    
    return fig_to_base64(fig)

def generar_grafico_tendencia(df):
    """Gráfico de líneas para la evolución anual."""
    if df.empty: return None
    
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    df_anual = df.groupby('Mes', sort=False)[['Temperatura Maxima', 'Temperatura Minima']].mean().reindex(orden_meses)

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.lineplot(data=df_anual, markers=True, dashes=False, ax=ax)
    ax.set_title(f"Tendencia Anual: {df['Ubicacion'].iloc[0]}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Promedio Mensual (°C)")
    ax.set_xlabel("Meses")
    
    # Rotación de etiquetas compatible con Figure
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    
    return fig_to_base64(fig)

def generar_grafico_comparativo(df1, df2, mes):
    """Compara dos ubicaciones en un mes específico."""
    df1_mes = df1[df1['Mes'] == mes.capitalize()]
    df2_mes = df2[df2['Mes'] == mes.capitalize()]
    
    df_comp = pd.concat([df1_mes, df2_mes])
    if df_comp.empty: return None

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.lineplot(data=df_comp, x='Dia', y='Temperatura Maxima', hue='Ubicacion', ax=ax, style='Ubicacion', markers=True)
    ax.set_title(f"Comparativa de Temperaturas: {mes}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Temperatura Máxima (°C)")
    
    return fig_to_base64(fig)