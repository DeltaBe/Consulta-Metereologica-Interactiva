from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
]