from django.shortcuts import render

# Create your views here.
from .utils import consultar_ciudades, obtener_grafico_base64

def index(request):
    ciudades = consultar_ciudades()
    grafico = None
    error = None

    if request.method == 'GET' and 'ciudad' in request.GET:
        ciudad = request.GET.get('ciudad')
        mes = request.GET.get('mes').capitalize()
        
        grafico = obtener_grafico_base64(ciudad, mes)
        if not grafico:
            error = f"No hay datos para {ciudad} en {mes}."

    context = {
        'ciudades': ciudades,
        'grafico': grafico,
        'error': error
    }
    return render(request, 'index.html', context)