from django.urls import path
from . import views


    #'' los colocamos vacios para que se refiera al index
    # views.funcion aca le decimos que del archivo views estamos llamando la funcion en este caso estamos llamando index
    #name='nombre' aca ponemos un nombre de referencia
urlpatterns = [
    path('', views.index, name='index'),
    path('configurar/', views.configurar, name='configurar'),
    path('visualizarXML/', views.visualizarXML, name='visualizarXML'),
    path('subirXML/', views.subirXML, name='subirXML'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('datos_estudiante/', views.datos_estudiante, name='datos_estudiante'),
    path('doc/', views.doc, name='doc'),
    path('peticiones/', views.peticiones, name='peticiones'),
]