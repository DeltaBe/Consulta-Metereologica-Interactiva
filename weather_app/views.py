from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import (
    obtener_datos_meteorologicos, 
    obtener_resumen_estadistico,
    generar_grafico_individual, 
    generar_grafico_tendencia, 
    generar_grafico_comparativo
)
from datetime import datetime

def index(request):
    # 1. Captura de parámetros básicos
    tab = request.GET.get('tab', 'individual')
    anio = request.GET.get('anio', '2024')
    pais = request.GET.get('pais', '').strip()
    estado = request.GET.get('estado', '').strip()
    mes = request.GET.get('mes', '').capitalize()

    # Variables de salida
    grafico = None
    resumen = None
    error = None

    # 2. Lógica por Pestaña
    try:
        if tab == 'individual' and estado and pais:
            df = obtener_datos_meteorologicos(estado, pais, anio)
            if not df.empty:
                if not mes: mes = "Enero" # Mes por defecto si no se ingresa
                grafico = generar_grafico_individual(df, mes)
                resumen = obtener_resumen_estadistico(df, mes)
                if not grafico: error = f"No hay datos para el mes de {mes}."
            else:
                error = f"No se encontraron datos para {estado}, {pais} en {anio}."

        elif tab == 'tendencia' and estado and pais:
            df = obtener_datos_meteorologicos(estado, pais, anio)
            if not df.empty:
                grafico = generar_grafico_tendencia(df)
                resumen = obtener_resumen_estadistico(df) # Resumen anual
            else:
                error = f"No se pudieron generar tendencias para {estado}."

        elif tab == 'comparativa':
            e1 = request.GET.get('estado1', '').strip()
            p1 = request.GET.get('pais1', '').strip()
            e2 = request.GET.get('estado2', '').strip()
            p2 = request.GET.get('pais2', '').strip()
            mes_comp = request.GET.get('mes_comp', 'Enero').capitalize()

            if e1 and e2:
                df1 = obtener_datos_meteorologicos(e1, p1, anio)
                df2 = obtener_datos_meteorologicos(e2, p2, anio)
                if not df1.empty and not df2.empty:
                    grafico = generar_grafico_comparativo(df1, df2, mes_comp)
                else:
                    error = "Uno o ambos estados no devolvieron datos."

    except Exception as e:
        error = f"Ocurrió un error inesperado: {str(e)}"

    context = {
        'tab_activa': tab,
        'grafico': grafico,
        'resumen': resumen,
        'error': error,
        'params': {
            'pais': pais,
            'estado': estado,
            'anio': anio,
            'mes': mes
        }
    }
    return render(request, 'index.html', context)

def exportar_pdf(request):
    tab = request.GET.get('tab', 'individual')
    anio = request.GET.get('anio', '2024')
    
    grafico = None
    titulo = "Reporte Meteorológico"
    mes_reporte = ""

    # Replicamos la lógica para obtener el gráfico que se ve en pantalla
    if tab == 'individual':
        estado = request.GET.get('estado', '').strip()
        pais = request.GET.get('pais', '').strip()
        mes_reporte = request.GET.get('mes', 'Enero').capitalize()
        df = obtener_datos_meteorologicos(estado, pais, anio)
        if not df.empty:
            grafico = generar_grafico_individual(df, mes_reporte)
            titulo = f"Análisis de Temperatura: {estado}, {pais}"

    elif tab == 'tendencia':
        estado = request.GET.get('estado', '').strip()
        pais = request.GET.get('pais', '').strip()
        df = obtener_datos_meteorologicos(estado, pais, anio)
        if not df.empty:
            grafico = generar_grafico_tendencia(df)
            titulo = f"Tendencia Anual: {estado}"

    elif tab == 'comparativa':
        e1 = request.GET.get('estado1', '').strip()
        p1 = request.GET.get('pais1', '').strip()
        e2 = request.GET.get('estado2', '').strip()
        p2 = request.GET.get('pais2', '').strip()
        mes_reporte = request.GET.get('mes_comp', 'Enero').capitalize()
        df1 = obtener_datos_meteorologicos(e1, p1, anio)
        df2 = obtener_datos_meteorologicos(e2, p2, anio)
        if not df1.empty and not df2.empty:
            grafico = generar_grafico_comparativo(df1, df2, mes_reporte)
            titulo = f"Comparativa: {e1} vs {e2}"

    # Fecha del reporte
    ahora = datetime.now()
    meses_esp = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha_hoy = f"{ahora.day} de {meses_esp[ahora.month - 1]} de {ahora.year}"

    context = {
        'grafico': grafico,
        'titulo': titulo,
        'mes': mes_reporte,
        'fecha_reporte': fecha_hoy,
        'anio': anio
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tab}_{anio}.pdf"'
    
    template = get_template('pdf_template.html')
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response