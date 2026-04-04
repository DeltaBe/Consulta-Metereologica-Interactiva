import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from matplotlib.figure import Figure

# Configuración estética de Seaborn
sns.set_theme(style="whitegrid")

# --- 1. FUNCIONES DE LLAMADA A API (GEOPOSICIONAMIENTO Y CLIMA) ---

def obtener_coordenadas(ciudad, pais):
    """Convierte el texto de ciudad y país en Latitud y Longitud."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={ciudad}&count=1&language=es&format=json"
        response = requests.get(url)
        data = response.json()
        if "results" in data:
            res = data["results"][0]
            return res["latitude"], res["longitude"]
    except Exception as e:
        print(f"Error en Geocoding: {e}")
    return None, None

def obtener_datos_meteorologicos(ciudad, pais, anio):
    """Obtiene el historial de todo un año desde la nube."""
    lat, lon = obtener_coordenadas(ciudad, pais)
    if lat is None:
        return pd.DataFrame()

    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={anio}-01-01&end_date={anio}-12-31&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        response = requests.get(url)
        data = response.json()
        
        df = pd.DataFrame({
            'Fecha': pd.to_datetime(data['daily']['time']),
            'Temperatura Maxima': data['daily']['temperature_2m_max'],
            'Temperatura Minima': data['daily']['temperature_2m_min'],
            'Ciudad': ciudad.capitalize()
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
    """Calcula KPIs basados en el DataFrame obtenido de la API."""
    if df.empty: return None
    
    df_filtrado = df.copy()
    if mes and mes.strip():
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes.capitalize()]
    
    if df_filtrado.empty: return None

    return {
        'max_abs': df_filtrado['Temperatura Maxima'].max(),
        'min_abs': df_filtrado['Temperatura Minima'].min(),
        'promedio': round(df_filtrado['Temperatura Maxima'].mean(), 1),
        'variabilidad': round(df_filtrado['Temperatura Maxima'].std(), 1) if not mes else None
    }

# --- 3. FUNCIONES DE GENERACIÓN DE GRÁFICOS (MATPLOTLIB/SEABORN) ---

def fig_to_base64(fig):
    """Convierte un objeto Figure de Matplotlib a cadena Base64."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_grafico_individual(df, mes):
    """Genera gráfico de barras para un mes específico."""
    df_mes = df[df['Mes'] == mes.capitalize()]
    if df_mes.empty: return None

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.barplot(data=df_mes, x='Dia', y='Temperatura Maxima', ax=ax, palette='Oranges')
    ax.set_title(f"Temperaturas Máximas en {mes} ({df_mes['Ciudad'].iloc[0]})", fontsize=14, fontweight='bold')
    ax.set_xlabel("Día del Mes")
    ax.set_ylabel("Temperatura (°C)")
    
    return fig_to_base64(fig)

def generar_grafico_tendencia(df):
    """Genera gráfico de líneas para la evolución anual."""
    if df.empty: return None
    
    # Agrupamos por mes para suavizar la línea
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    df_anual = df.groupby('Mes', sort=False)[['Temperatura Maxima', 'Temperatura Minima']].mean().reindex(orden_meses)

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.lineplot(data=df_anual, markers=True, dashes=False, ax=ax)
    ax.set_title(f"Tendencia Anual: {df['Ciudad'].iloc[0]}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Promedio Mensual (°C)")
    ax.set_xlabel("Meses")
    plt.setp(ax.get_xticklabels(), rotation=45)
    
    return fig_to_base64(fig)

def generar_grafico_comparativo(df1, df2, mes):
    """Compara dos ciudades en un mes específico."""
    df1_mes = df1[df1['Mes'] == mes.capitalize()]
    df2_mes = df2[df2['Mes'] == mes.capitalize()]
    
    df_comp = pd.concat([df1_mes, df2_mes])
    if df_comp.empty: return None

    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    sns.lineplot(data=df_comp, x='Dia', y='Temperatura Maxima', hue='Ciudad', ax=ax, style='Ciudad', markers=True)
    ax.set_title(f"Comparativa de Temperaturas: {mes}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Temperatura Máxima (°C)")
    
    return fig_to_base64(fig)