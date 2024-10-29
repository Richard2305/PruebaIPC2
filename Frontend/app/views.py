from django.shortcuts import render
from .forms import FileForm
import requests
import xml.etree.ElementTree as ET
import graphviz

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
    graph_image_path = None
    departamentos_guatemala = [
        "Alta Verapaz", "Baja Verapaz", "Chimaltenango", "Chiquimula", "Guatemala",
        "El Progreso", "Escuintla", "Huehuetenango", "Izabal", "Jalapa", "Jutiapa",
        "Petén", "Quetzaltenango", "Quiché", "Retalhuleu", "Sacatepéquez",
        "San Marcos", "Santa Rosa", "Sololá", "Suchitepéquez", "Totonicapán", "Zacapa"
    ]

    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']
            xml_content = file.read().decode('utf-8')

            try:
                # Parsear el contenido XML
                root = ET.fromstring(xml_content)
                ventas_guatemala = []

                # Filtrar las ventas que son de departamentos de Guatemala
                for venta in root.findall(".//Venta"):
                    departamento = venta.get('departamento')
                    if departamento in departamentos_guatemala:
                        fecha = venta.find('Fecha').text
                        ventas_guatemala.append({'departamento': departamento, 'fecha': fecha})

                # Crear un gráfico dirigido con las ventas filtradas (opcional)
                dot = graphviz.Digraph(comment="Ventas en Guatemala")

                for idx, venta in enumerate(ventas_guatemala):
                    node_id = f"venta_{idx}"
                    dot.node(node_id, f"{venta['departamento']} - {venta['fecha']}")

                # Guardar el gráfico en un archivo temporal
                graph_image_path = "static/graph_xml"
                dot.render(graph_image_path, format="png")
                graph_image_path += ".png"
                
                # Pasar las ventas filtradas al contexto para mostrar en la interfaz
                xml_content = ET.tostring(root, encoding='utf8').decode('utf8')
            except ET.ParseError as e:
                print(f"Error al parsear el XML: {e}")

    return render(request, 'configurar.html', {
        'xml_content': xml_content,
        'graph_image_path': graph_image_path,
        'ventas_guatemala': ventas_guatemala
    })

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

