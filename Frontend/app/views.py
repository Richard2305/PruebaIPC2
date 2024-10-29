from django.shortcuts import render
from .forms import FileForm
import requests
import xml.etree.ElementTree as ET

from datetime import datetime
import re
from django.shortcuts import render
from django.http import JsonResponse


api = 'http://localhost:5000'

# Create your views here.
def index(request):
    return render(request, 'index.html')

def cardsPizza(request):
    context = {
        'pizzas': None
    }

    response = requests.get(api+'/config/obtenerPizzas')

    if response.status_code == 200:
        context['pizzas'] = response.json()['pizzas']
        return render(request, 'cardsPizza.html', context)
    else:
        context['pizzas'] = []
        return render(request, 'cardsPizza.html')

def verPizzaDetalle(request, id):
    context = {
        'pizzas': None
    }

    response = requests.get(api+'/config/obtenerPizza/'+id)
    if response.status_code == 200:
        context['pizza'] = response.json()
        return render(request, 'detailPizza.html', context)
    else:
        context['pizzas'] = []
        return render(request, 'detailPizza.html')

def configurar(request):
    xmlContent = None
    return render(request, 'configurar.html', {'xmlContent': xmlContent})

def visualizarXML(request):
    xml_content = ""
    response_message = ""
    xml_output_content = ""

    if request.method == 'POST':
        xml_file = request.FILES.get("file")
        if xml_file:
            try:
                # Leer y procesar el archivo XML cargado
                xml_content = xml_file.read().decode("utf-8")
                root = ET.fromstring(xml_content)
                
                # Inicializar el elemento raíz para el XML de salida
                lista_respuestas = ET.Element('lista_respuestas')
                mensajes = root.find("lista_mensajes")

                if mensajes is not None:
                    # Agrupar mensajes por fecha
                    mensajes_por_fecha = {}
                    for mensaje in mensajes.findall("mensaje"):
                        texto_mensaje = mensaje.text
                        fecha_match = re.search(r'\d{2}/\d{2}/\d{4}', texto_mensaje)
                        fecha = fecha_match.group(0) if fecha_match else datetime.now().strftime("%d/%m/%Y")
                        
                        if fecha not in mensajes_por_fecha:
                            mensajes_por_fecha[fecha] = []
                        mensajes_por_fecha[fecha].append(texto_mensaje)

                    # Procesar cada grupo de mensajes por fecha
                    for fecha, mensajes_dia in mensajes_por_fecha.items():
                        respuesta = ET.SubElement(lista_respuestas, 'respuesta')
                        ET.SubElement(respuesta, 'fecha').text = fecha

                        total_mensajes, positivos, negativos, neutros = 0, 0, 0, 0
                        empresas_data = {}

                        for texto_mensaje in mensajes_dia:
                            total_mensajes += 1
                            sentimiento = "neutro"
                            if any(word in texto_mensaje.lower() for word in ["excelente", "bueno", "maravilloso"]):
                                sentimiento = "positivo"
                                positivos += 1
                            elif any(word in texto_mensaje.lower() for word in ["lamentable", "frustrante", "deficiente"]):
                                sentimiento = "negativo"
                                negativos += 1
                            else:
                                neutros += 1
                            
                            # Aquí debes adaptar para analizar empresas y servicios específicos
                            for empresa in root.findall(".//empresa"):
                                nombre_empresa = empresa.find('nombre').text.strip()
                                if nombre_empresa.lower() in texto_mensaje.lower():
                                    if nombre_empresa not in empresas_data:
                                        empresas_data[nombre_empresa] = {"total": 0, "positivos": 0, "negativos": 0, "neutros": 0, "servicios": {}}
                                    
                                    empresas_data[nombre_empresa]["total"] += 1
                                    empresas_data[nombre_empresa][sentimiento + "s"] += 1
                                    
                                    for servicio in empresa.find("servicios").findall("servicio"):
                                        nombre_servicio = servicio.get("nombre").strip()
                                        if any(alias.text.strip().lower() in texto_mensaje.lower() for alias in servicio.findall("alias")):
                                            if nombre_servicio not in empresas_data[nombre_empresa]["servicios"]:
                                                empresas_data[nombre_empresa]["servicios"][nombre_servicio] = {"total": 0, "positivos": 0, "negativos": 0, "neutros": 0}
                                            
                                            empresas_data[nombre_empresa]["servicios"][nombre_servicio]["total"] += 1
                                            empresas_data[nombre_empresa]["servicios"][nombre_servicio][sentimiento + "s"] += 1

                        # Añadir elementos de mensajes
                        mensajes_elemento = ET.SubElement(respuesta, 'mensajes')
                        ET.SubElement(mensajes_elemento, 'total').text = str(total_mensajes)
                        ET.SubElement(mensajes_elemento, 'positivos').text = str(positivos)
                        ET.SubElement(mensajes_elemento, 'negativos').text = str(negativos)
                        ET.SubElement(mensajes_elemento, 'neutros').text = str(neutros)

                        # Añadir elementos de analisis
                        analisis = ET.SubElement(respuesta, 'analisis')
                        for nombre_empresa, datos_empresa in empresas_data.items():
                            empresa_element = ET.SubElement(analisis, 'empresa', nombre=nombre_empresa)
                            empresa_mensajes = ET.SubElement(empresa_element, 'mensajes')
                            ET.SubElement(empresa_mensajes, 'total').text = str(datos_empresa["total"])
                            ET.SubElement(empresa_mensajes, 'positivos').text = str(datos_empresa["positivos"])
                            ET.SubElement(empresa_mensajes, 'negativos').text = str(datos_empresa["negativos"])
                            ET.SubElement(empresa_mensajes, 'neutros').text = str(datos_empresa["neutros"])

                            servicios_element = ET.SubElement(empresa_element, 'servicios')
                            for nombre_servicio, datos_servicio in datos_empresa["servicios"].items():
                                servicio_element = ET.SubElement(servicios_element, 'servicio', nombre=nombre_servicio)
                                servicio_mensajes = ET.SubElement(servicio_element, 'mensajes')
                                ET.SubElement(servicio_mensajes, 'total').text = str(datos_servicio["total"])
                                ET.SubElement(servicio_mensajes, 'positivos').text = str(datos_servicio["positivos"])
                                ET.SubElement(servicio_mensajes, 'negativos').text = str(datos_servicio["negativos"])
                                ET.SubElement(servicio_mensajes, 'neutros').text = str(datos_servicio["neutros"])

                # Convertir el XML de salida a cadena
                xml_output_content = ET.tostring(lista_respuestas, encoding='utf-8').decode('utf-8')
                response_message = "XML procesado correctamente y clasificado."

            except ET.ParseError as e:
                response_message = f"Error al parsear el XML: {e}"
            except Exception as e:
                response_message = f"Error: {e}"

    return render(request, 'configurar.html', {
        'xml_content': xml_content,
        'xml_output_content': xml_output_content,
        'response_message': response_message
    })

def clasificar_sentimiento(texto):
    if "excelente" in texto or "bueno" in texto or "maravilloso" in texto:
        return "positivo"
    elif "lamentable" in texto or "frustrante" in texto or "deficiente" in texto:
        return "negativo"
    else:
        return "neutro"

def group_messages_by_date(root):
    mensajes_por_fecha = {}
    
    for mensaje in root.findall(".//mensaje"):
        
        fecha_texto = mensaje.get("fecha", datetime.now().strftime("%d/%m/%Y"))
        fecha = datetime.strptime(fecha_texto, "%d/%m/%Y")
        if fecha not in mensajes_por_fecha:
            mensajes_por_fecha[fecha] = []
        mensajes_por_fecha[fecha].append(mensaje)
    return sorted(mensajes_por_fecha.items())



def subirXML(request):
    xml_content = ""
    response_message = ""
    departamentos_guatemala = [
        "Alta Verapaz", "Baja Verapaz", "Chimaltenango", "Chiquimula", "Guatemala",
        "El Progreso", "Escuintla", "Huehuetenango", "Izabal", "Jalapa", "Jutiapa",
        "Petén", "Quetzaltenango", "Quiché", "Retalhuleu", "Sacatepéquez",
        "San Marcos", "Santa Rosa", "Sololá", "Suchitepéquez", "Totonicapán", "Zacapa"
    ]

    if request.method == 'POST':
        xml_content = request.POST.get('xml', '')

        try:
            # Parsear el XML de entrada
            root = ET.fromstring(xml_content)
            
            # Crear la estructura del nuevo XML de salida
            resumen = ET.Element('Resumen')
            listado_ventas = ET.SubElement(resumen, 'ListadoVentas')

            # Filtrar las ventas que son de departamentos de Guatemala
            for venta in root.findall(".//Venta"):
                departamento = venta.get('departamento')
                if departamento in departamentos_guatemala:
                    fecha = venta.find('Fecha').text
                    # Agregar la venta al nuevo XML
                    nueva_venta = ET.SubElement(listado_ventas, 'Venta', {'departamento': departamento})
                    fecha_elemento = ET.SubElement(nueva_venta, 'Fecha')
                    fecha_elemento.text = fecha
            
            # Convertir el XML a string y formatearlo
            xml_string = ET.tostring(resumen, encoding='utf-8').decode('utf-8')
            response_message = "XML procesado correctamente y filtrado."
            xml_content = xml_string

        except ET.ParseError as e:
            response_message = f"Error al parsear el XML: {e}"

    return render(request, 'configurar.html', {
        'xml_content': xml_content,
        'response_message': response_message
    })

def ayuda(request):
    return render(request, 'ayuda.html')

def datos_estudiante(request):
    return render(request, 'datos_estudiante.html')

def doc(request):
    return render(request, 'doc.html')

# Variable global para cargar el último archivo de respuesta XML
ultimo_archivo_respuesta = None  # Asignar aquí el archivo XML de respuesta

def peticiones(request):
    global ultimo_archivo_respuesta

    if request.method == 'POST':
        opcion = request.POST.get('opcion')

        # 1. Consultar Datos
        if opcion == "consultar":
            with open(ultimo_archivo_respuesta, "r") as file:
                xml_data = file.read()
            return JsonResponse({"data": xml_data})

        # 2. Resumen de Clasificación por Fecha
        elif opcion == "resumen_fecha":
            fecha = request.POST.get('fecha')
            empresa = request.POST.get('empresa', "todas")
            datos = obtener_datos_por_fecha(fecha, empresa)
            return JsonResponse({"grafico_datos": datos})

        # 3. Resumen por Rango de Fechas
        elif opcion == "resumen_rango":
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            empresa = request.POST.get('empresa', "todas")
            datos = obtener_datos_por_rango(fecha_inicio, fecha_fin, empresa)
            return JsonResponse({"grafico_datos": datos})

    return render(request, 'peticiones.html')

# Función para obtener datos por rango de fechas
def obtener_datos_por_rango(fecha_inicio, fecha_fin, empresa):
    # Aquí extraes los datos entre las fechas indicadas en `ultimo_archivo_respuesta`
    # Abre y analiza el XML según el rango y empresa para crear un resumen.

    # Filtro según empresa si no es "todas"
    if empresa.lower() != "todas":
        datos_rango = [dato for dato in datos_rango if dato["empresa"].lower() == empresa.lower()]

    return datos_rango

