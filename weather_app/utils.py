import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib, base64

# Configuración para que Matplotlib no intente abrir ventanas (Modo No Interactivo)
import matplotlib
matplotlib.use('Agg') 

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

def consultar_ciudades():
    df = cargar_dataframe()
    if df.empty:
        return []
    return sorted(df['Ciudad'].unique().tolist())

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

def obtener_grafico_base64(ciudad, mes):
    df_mes_ciudad = dataframe_mes_ciudad() 
    
    # Filtrar por ciudad y mes
    df_filtrado = df_mes_ciudad[(df_mes_ciudad['Ciudad'] == ciudad) & 
                                (df_mes_ciudad['Mes'] == mes)]

    if not df_filtrado.empty:
        # 1. Crear la figura
        plt.figure(figsize=(8, 5))
        categorias = ['Máxima', 'Mínima']
        
        # Tomamos el promedio si hay varios registros, o el primero
        max_temp = df_filtrado['Temperatura Maxima'].mean()
        min_temp = df_filtrado['Temperatura Minima'].mean()
        valores = [max_temp, min_temp]

        barras = plt.bar(categorias, valores, color=['#ff4d4d', '#3399ff'])

        # Estética del gráfico
        plt.title(f'Temperaturas en {ciudad} ({mes})', fontsize=14)
        plt.ylabel('Grados Celsius (°C)')
        plt.ylim(0, max(valores) + 10) 

        # Añadir etiquetas de valor sobre las barras
        for barra in barras:
            yval = barra.get_height()
            plt.text(barra.get_x() + barra.get_width()/2, yval + 0.5, f'{yval:.1f}°', ha='center', va='bottom')

        # 2. Guardar el gráfico en un buffer de memoria (BytesIO)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        # 3. Codificar el contenido del buffer a Base64
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
        
        plt.close() # MUY IMPORTANTE: Cerrar la figura para no agotar la RAM del servidor
        return uri
    
    return None