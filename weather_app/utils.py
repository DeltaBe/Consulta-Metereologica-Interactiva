import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib, base64
import seaborn as sns
# Configuración para que Matplotlib no intente abrir ventanas (Modo No Interactivo)
import matplotlib
matplotlib.use('Agg') 
# Función para cargar el DataFrame de los datos

sns.set_theme(style="whitegrid", palette="muted")
def cargar_dataframe():
    # Nota: Asegúrate de que esta ruta sea correcta en tu PC
    path = r"C:\Users\elver\Documents\cursos\data science federico\archivos csv\Datos+Meteorológicos_Arg_2023.csv"
    try:
        df = pd.read_csv(path)
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, format='%d/%m/%Y')
        df['Mes_Num'] = df['Fecha'].dt.month
        return df
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en {path}")
        return pd.DataFrame()
# Función para obtener una lista de ciudades
def consultar_ciudades():
    df = cargar_dataframe()
    if df.empty:
        return []
    return sorted(df['Ciudad'].unique().tolist())
# Función para obtener un DataFrame con los datos de un mes y ciudad
def dataframe_mes_ciudad():
    datos = cargar_dataframe()
    if datos.empty:
        return pd.DataFrame()

    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    df_resumen = datos[['Ciudad', 'Temperatura Maxima', 'Temperatura Minima', 'Mes_Num', 'Fecha']].copy()
    df_resumen['Mes'] = df_resumen['Mes_Num'].map(meses_es)
    
    # Retornamos el DataFrame con los nombres de meses
    return df_resumen[['Ciudad', 'Mes', 'Temperatura Maxima', 'Temperatura Minima', 'Fecha']]

# Función para obtener la gráfica de un mes y ciudad
def obtener_grafico_base64(ciudad, mes):
    df_mes_ciudad = dataframe_mes_ciudad() 
    df_filtrado = df_mes_ciudad[(df_mes_ciudad['Ciudad'] == ciudad) & 
                                (df_mes_ciudad['Mes'] == mes)]

    if not df_filtrado.empty:
        plt.figure(figsize=(8, 5))
        
        # Preparamos los datos para Seaborn (necesita formato largo)
        datos_plot = pd.DataFrame({
            'Tipo': ['Máxima', 'Mínima'],
            'Temperatura': [df_filtrado['Temperatura Maxima'].mean(), 
                           df_filtrado['Temperatura Minima'].mean()]
        })

        # Creamos el gráfico con Seaborn
        ax = sns.barplot(x='Tipo', y='Temperatura', data=datos_plot, hue='Tipo', palette=['#FF5733', '#33C1FF'], legend=False)

        # Mejoras estéticas de Seaborn
        plt.title(f'Temperaturas en {ciudad} ({mes})', fontsize=15, pad=20, fontweight='bold')
        plt.ylabel('Grados Celsius (°C)', fontsize=12)
        plt.xlabel('', fontsize=12)
        sns.despine(left=True, bottom=True) # Quita los bordes innecesarios

        # Etiquetas de valor sobre las barras
        for p in ax.patches:
            ax.annotate(f'{p.get_height():.1f}°', 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha='center', va='center', 
                        xytext=(0, 9), 
                        textcoords='offset points',
                        fontsize=11, fontweight='bold')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        uri = urllib.parse.quote(base64.b64encode(buf.read()))
        plt.close()
        return uri
    return None


# Función para obtener la gráfica de comparación de dos ciudades
def obtener_grafico_comparativo_base64(ciudades_lista, mes):
    df_mes_ciudad = dataframe_mes_ciudad()
    df_filtrado = df_mes_ciudad[(df_mes_ciudad['Ciudad'].isin(ciudades_lista)) & 
                                (df_mes_ciudad['Mes'] == mes)]
    
    if not df_filtrado.empty:
        plt.figure(figsize=(10, 6))
        
        # Convertir a formato "tidy" para que Seaborn lo entienda mejor
        df_tidy = df_filtrado.melt(id_vars=['Ciudad'], 
                                   value_vars=['Temperatura Maxima', 'Temperatura Minima'],
                                   var_name='Tipo', value_name='Temp')

        # Gráfico comparativo elegante
        ax = sns.barplot(x='Ciudad', y='Temp', hue='Tipo', data=df_tidy, palette=['#FF5733', '#33C1FF'])

        plt.title(f'Comparativa de Temperaturas - {mes}', fontsize=16, fontweight='bold', pad=20)
        plt.ylabel('Temperatura (°C)', fontsize=12)
        plt.legend(title='Medición', frameon=True, shadow=True)
        sns.despine()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        uri = urllib.parse.quote(base64.b64encode(buf.read()))
        plt.close()
        return uri
    return None



def obtener_grafico_tendencia_base64(ciudad):
    df_resumen = dataframe_mes_ciudad()
    # Filtrar solo por ciudad para tener todo el año
    df_ciudad = df_resumen[df_resumen['Ciudad'] == ciudad].copy()
    
    # Ordenar cronológicamente por la columna Fecha para que la línea no salte
    df_ciudad = df_ciudad.sort_values('Fecha')

    if not df_ciudad.empty:
        plt.figure(figsize=(12, 6))
        
        # Graficamos la tendencia con Seaborn
        # lineplot calcula automáticamente la media y la sombra de desviación (ci)
        sns.lineplot(data=df_ciudad, x='Mes', y='Temperatura Maxima', 
                     label='Tendencia Máxima', color='#FF5733', marker='o', errorbar='sd')
        
        sns.lineplot(data=df_ciudad, x='Mes', y='Temperatura Minima', 
                     label='Tendencia Mínima', color='#33C1FF', marker='o', errorbar='sd')

        # Estética profesional
        plt.title(f'Tendencia Anual y Desviación - {ciudad} (2023)', fontsize=16, fontweight='bold', pad=20)
        plt.ylabel('Temperatura (°C)', fontsize=12)
        plt.xlabel('Meses del Año', fontsize=12)
        plt.xticks(rotation=45) # Inclinar meses para mejor lectura
        plt.legend(frameon=True, shadow=True)
        
        sns.despine()
        plt.tight_layout()

        # Conversión a Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
        buf.seek(0)
        uri = urllib.parse.quote(base64.b64encode(buf.read()))
        plt.close()
        return uri
    return None


def obtener_resumen_estadistico(ciudad_nombre, mes=None):
    try:
        df = cargar_dataframe()
        df_filtrado = df[df['Ciudad'] == ciudad_nombre]
        
        # Si el usuario seleccionó un mes, filtramos el DataFrame
        if mes and mes.strip():
            df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
            titulo = f"Métricas de {mes}"
            mostrar_ds = False # En mes individual no mostramos desviación
        else:
            titulo = "Resumen Anual"
            mostrar_ds = True

        if df_filtrado.empty:
            return None
            
        return {
            'max_abs': df_filtrado['Temperatura Maxima'].max(),
            'min_abs': df_filtrado['Temperatura Minima'].min(),
            'promedio': round(df_filtrado['Temperatura Maxima'].mean(), 1),
            'variabilidad': round(df_filtrado['Temperatura Maxima'].std(), 1) if mostrar_ds else None,
            'titulo': titulo
        }
    except Exception as e:
        print(f"Error: {e}")
        return None