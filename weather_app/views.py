from django.shortcuts import render , redirect
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
# Create your views here.
from .utils import consultar_ciudades, obtener_grafico_base64 , obtener_grafico_comparativo_base64 , obtener_grafico_tendencia_base64 , obtener_resumen_estadistico
from datetime import datetime

# Función para renderizar la página principal
def index(request):
    # 1. Preparación inicial
    ciudades = consultar_ciudades()
    tab = request.GET.get('tab', 'individual')
    grafico = None
    error = None
    resumen = None  
    ciudad_seleccionada = None

    # 2. Lógica por pestañas
    if tab == 'individual' and 'ciudad' in request.GET:
        ciudad_seleccionada = request.GET.get('ciudad')
        mes_input = request.GET.get('mes')
        mes = mes_input.capitalize() if mes_input else ""
        
        grafico = obtener_grafico_base64(ciudad_seleccionada, mes)
        
        # CÁLCULO MENSUAL: Pasamos el mes para que las tarjetas cambien
        if grafico:
            resumen = obtener_resumen_estadistico(ciudad_seleccionada, mes=mes)

    elif tab == 'comparativa' and 'ciudad1' in request.GET:
        c1 = request.GET.get('ciudad1')
        c2 = request.GET.get('ciudad2')
        mes_input = request.GET.get('mes_comp')
        mes = mes_input.capitalize() if mes_input else ""
        
        if c1 == c2:
            error = "Selecciona dos ciudades distintas para comparar."
        else:
            grafico = obtener_grafico_comparativo_base64([c1, c2], mes)
            # Quitamos el resumen en comparativa como solicitaste
            resumen = None 

    elif tab == 'tendencia' and 'ciudad_t' in request.GET:
        ciudad_seleccionada = request.GET.get('ciudad_t')
        grafico = obtener_grafico_tendencia_base64(ciudad_seleccionada)
        
        # CÁLCULO ANUAL: No pasamos mes, para que calcule todo el año y muestre desviación
        if grafico:
            resumen = obtener_resumen_estadistico(ciudad_seleccionada)

    # 3. Manejo de errores de visualización
    if not grafico and any(k in request.GET for k in ['ciudad', 'ciudad1', 'ciudad_t']):
        error = error or "No se encontraron datos para la selección realizada."

    # 4. Envío de contexto al Template
    context = {
        'ciudades': ciudades,
        'grafico': grafico,
        'error': error,
        'tab_activa': tab,
        'resumen': resumen  
    }
    
    return render(request, 'index.html', context)

def exportar_pdf(request):
    tab = request.GET.get('tab', 'individual')
    ciudad = request.GET.get('ciudad')
    mes = request.GET.get('mes', '').capitalize()
    
    # Obtenemos el gráfico según la pestaña
    if tab == 'individual':
        grafico = obtener_grafico_base64(ciudad, mes)
        titulo = f"Reporte Meteorológico: {ciudad}"
    else:
        c1 = request.GET.get('ciudad1')
        c2 = request.GET.get('ciudad2')
        mes = request.GET.get('mes_comp', '').capitalize()
        grafico = obtener_grafico_comparativo_base64([c1, c2], mes)
        titulo = f"Comparativa: {c1} vs {c2}"

    # 1. Obtener la fecha actual
    ahora = datetime.now()
    
    # 2. Diccionario manual de meses en español
    meses_esp = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    
    # 3. Construir la cadena de texto: "03 de Abril de 2026"
    fecha_hoy = f"{ahora.day} de {meses_esp[ahora.month - 1]} de {ahora.year}"
    
    context = {
        'grafico': grafico,
        'titulo': titulo,
        'mes': mes,
        'fecha_reporte': fecha_hoy
    }

    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{mes}.pdf"'
    
    template = get_template('pdf_template.html')
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response