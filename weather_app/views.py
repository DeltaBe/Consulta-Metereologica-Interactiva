from django.shortcuts import render

# Create your views here.
from .utils import consultar_ciudades, obtener_grafico_base64 , obtener_grafico_comparativo_base64

# Función para renderizar la página principal
def index(request):
    ciudades = consultar_ciudades()
    tab = request.GET.get('tab', 'individual') # Detectar pestaña activa
    grafico = None
    error = None
    # Procesar datos de la página para realizar una visualizacion de los datos
    if tab == 'individual' and 'ciudad' in request.GET:
        ciudad = request.GET.get('ciudad')
        mes = request.GET.get('mes').capitalize()
        grafico = obtener_grafico_base64(ciudad, mes)
    # Procesar datos de la página para realizar una comparación de dos ciudades
    elif tab == 'comparativa' and 'ciudad1' in request.GET:
        c1 = request.GET.get('ciudad1')
        c2 = request.GET.get('ciudad2')
        mes = request.GET.get('mes_comp').capitalize()
        if c1 == c2:
            error = "Selecciona dos ciudades distintas para comparar."
        else:
            grafico = obtener_grafico_comparativo_base64([c1, c2], mes)
    # Si no se detectaron datos, mostrar un mensaje de error
    if not grafico and (request.GET.get('ciudad') or request.GET.get('ciudad1')):
        error = error or "No se encontraron datos para la selección."

    context = {
        'ciudades': ciudades,
        'grafico': grafico,
        'error': error,
        'tab_activa': tab
    }
    return render(request, 'index.html', context)