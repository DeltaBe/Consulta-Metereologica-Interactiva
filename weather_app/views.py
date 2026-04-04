from django.shortcuts import render , redirect
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
# Create your views here.

from datetime import datetime

from .utils import (
    obtener_datos_meteorologicos,
    generar_grafico_individual,
    generar_grafico_tendencia,
    generar_grafico_comparativo,
    obtener_resumen_estadistico
)

def index(request):
    # 1. Parámetros base desde el navegador
    tab = request.GET.get('tab', 'individual')
    pais = request.GET.get('pais', '').strip()
    ciudad = request.GET.get('ciudad', '').strip()
    anio = request.GET.get('anio', '2023') # Año por defecto
    mes_input = request.GET.get('mes', '').strip()
    mes = mes_input.capitalize() if mes_input else ""

    # Variables de respuesta
    grafico = None
    error = None
    resumen = None

    # --- LÓGICA POR PESTAÑA ---

    # PESTAÑA INDIVIDUAL
    if tab == 'individual' and ciudad and pais:
        df = obtener_datos_meteorologicos(ciudad, pais, anio)
        if not df.empty:
            if mes:
                grafico = generar_grafico_individual(df, mes)
                resumen = obtener_resumen_estadistico(df, mes)
            else:
                error = "Por favor, escribe un mes (ej: Mayo) para el análisis individual."
        else:
            error = f"No se encontraron datos para {ciudad}, {pais} en el año {anio}."

    # PESTAÑA COMPARATIVA
    elif tab == 'comparativa':
        c1 = request.GET.get('ciudad1', '').strip()
        p1 = request.GET.get('pais1', '').strip()
        c2 = request.GET.get('ciudad2', '').strip()
        p2 = request.GET.get('pais2', '').strip()
        mes_comp = request.GET.get('mes_comp', '').capitalize()

        if all([c1, p1, c2, p2, mes_comp]):
            df1 = obtener_datos_meteorologicos(c1, p1, anio)
            df2 = obtener_datos_meteorologicos(c2, p2, anio)
            
            if not df1.empty and not df2.empty:
                grafico = generar_grafico_comparativo(df1, df2, mes_comp)
                # Omitimos resumen en comparativa por diseño
            else:
                error = "Error al obtener datos de una o ambas ciudades."
        elif any([c1, p1, c2, p2]):
            error = "Completa todos los campos de ambas ciudades y el mes."

    # PESTAÑA TENDENCIA
    elif tab == 'tendencia' and ciudad and pais:
        df = obtener_datos_meteorologicos(ciudad, pais, anio)
        if not df.empty:
            grafico = generar_grafico_tendencia(df)
            resumen = obtener_resumen_estadistico(df) # Anual (sin mes)
        else:
            error = f"No se pudo generar la tendencia para {ciudad}."

    # --- CONTEXTO PARA EL TEMPLATE ---
    context = {
        'tab_activa': tab,
        'grafico': grafico,
        'error': error,
        'resumen': resumen,
        # Devolvemos los datos para mantener los inputs llenos
        'params': {
            'pais': pais,
            'ciudad': ciudad,
            'anio': anio,
            'mes': mes
        }
    }
    
    return render(request, 'index.html', context)

def exportar_pdf(request):
    # 1. Parámetros desde la URL
    tab = request.GET.get('tab', 'individual')
    anio = request.GET.get('anio', '2023')
    
    grafico = None
    titulo = ""
    mes = ""

    # 2. Lógica según la pestaña para obtener datos de la API y generar gráfico
    if tab == 'individual':
        ciudad = request.GET.get('ciudad', '').strip()
        pais = request.GET.get('pais', '').strip()
        mes = request.GET.get('mes', '').capitalize()
        
        # Llamamos a la API para tener el DataFrame
        df = obtener_datos_meteorologicos(ciudad, pais, anio)
        if not df.empty:
            grafico = generar_grafico_individual(df, mes)
            titulo = f"Reporte Meteorológico: {ciudad.capitalize()} ({pais.capitalize()})"
        else:
            titulo = "Error: No se encontraron datos para el reporte."

    elif tab == 'comparativa':
        c1 = request.GET.get('ciudad1', '').strip()
        p1 = request.GET.get('pais1', '').strip()
        c2 = request.GET.get('ciudad2', '').strip()
        p2 = request.GET.get('pais2', '').strip()
        mes = request.GET.get('mes_comp', '').capitalize()
        
        # Obtenemos ambos DataFrames de la API
        df1 = obtener_datos_meteorologicos(c1, p1, anio)
        df2 = obtener_datos_meteorologicos(c2, p2, anio)
        
        if not df1.empty and not df2.empty:
            grafico = generar_grafico_comparativo(df1, df2, mes)
            titulo = f"Comparativa: {c1.capitalize()} vs {c2.capitalize()}"
        else:
            titulo = "Error: Datos insuficientes para la comparativa."

    # 3. Fecha del reporte en español
    ahora = datetime.now()
    meses_esp = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    fecha_hoy = f"{ahora.day} de {meses_esp[ahora.month - 1]} de {ahora.year}"

    # 4. Contexto para el template HTML
    context = {
        'grafico': grafico,
        'titulo': titulo,
        'mes': mes,
        'fecha_reporte': fecha_hoy,
        'anio': anio
    }

    # 5. Generar el PDF usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    # Nombre de archivo dinámico
    filename = f"reporte_{ciudad if tab=='individual' else 'comparativa'}_{mes}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    template = get_template('pdf_template.html')
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    
    return response