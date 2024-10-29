from xml.dom import minidom
from flask import Flask, jsonify, request
from flask_cors import CORS
import xml.etree.ElementTree as ET
import re


#  FLask App
app = Flask(__name__)
CORS(app)

listadoUsuarios = []
listadoPizzas = []

mensaje = ""
listadoPositivas = []
listadoNegativas = []
listadoEmpresas = []

posiblesEstados = {0: "Positivo", 1: "Negativo", 2: "Neutro"}

# Clases
class Usuario:
    def __init__(self, usuario, fechaCreacion, password, rol):
        self.usuario = usuario
        self.fechaCreacion = fechaCreacion
        self.password = password
        self.rol = rol

class Empresa:
    def __init__(self, nombre):
        self.nombre = nombre
        self.servicios = []

    def __str__(self):
        return f'Empresa: {self.nombre}, Servicios: {self.servicios}'
    
    def to_dict(self):
        return {
            'nombre': self.nombre,
            'servicios': [servicio.__dict__ for servicio in self.servicios]
        }

class Servicio:
    def __init__(self, nombre):
        self.nombre = nombre
        self.alias = []

    def  __str__(self):
        return f'Servicio: {self.nombre}, Alias: {self.alias}'

    def to_dict(self):
        return {
            'nombre': self.nombre,
            'alias': self.alias
        }

# Routes
@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/api', methods=['GET'])
def api():
    return jsonify({'message': 'Hello, World!'})

@app.route('/config/obtenerUsuarios', methods=['GET'])
def getUsuarios():
    usuarios = []
    for usuario in listadoUsuarios:
        usuarios.append({'usuario': usuario.usuario, 'fechaCreacion': usuario.fechaCreacion, 'rol': usuario.rol})

    return jsonify({'usuarios': usuarios})

@app.route('/config/postXML', methods=['POST'])
def postXML():
    data = request.get_data()
    root = ET.fromstring(data)

    for configListado in root:
        for config in configListado:
            if config.tag == 'Usuario':
                username = config.get('user')
                fechaCreacion = config.find('fecha_creacion').text
                password = config.find('password').text
                rol = config.find('rol').text

                patron_fecha = r'\b(\d{2}/\d{2}/\d{4})\b'
                fechaGuardar = re.search(patron_fecha, fechaCreacion)

                if fechaGuardar:
                    usuario = Usuario(username, fechaGuardar.group(), password, rol)
                    listadoUsuarios.append(usuario)
                else:
                    return jsonify({'message': 'Fecha incorrecta'})

            if config.tag == 'Pizza':
                nombre = config.find('nombre').text
                precio = config.find('precio').text
                ingredientes = config.find('ingredientes').text
                imagen = config.find('imagen').text

                pizza = Pizza(nombre, precio, ingredientes, imagen)
                listadoPizzas.append(pizza)

    return jsonify({'message': 'XML recibido'})


@app.route('/config/obtenerPizzas', methods=['GET'])
def getPizzas():
    pizzas = []
    for pizza in listadoPizzas:
        pizzas.append({'id':pizza.id, 'nombre': pizza.nombre, 'precio': pizza.precio, 'ingredientes': pizza.ingredientes, 'imagen': pizza.imagen})

    return jsonify({'pizzas': pizzas})

    
@app.route('/config/obtenerPizza/<id>', methods=['GET'])
def getPizza(id):
    for pizza in listadoPizzas:
        if pizza.id == int(id):
            return jsonify({'nombre': pizza.nombre, 'precio': pizza.precio, 'ingredientes': pizza.ingredientes, 'imagen': pizza.imagen})

    return jsonify({'message': 'Pizza no encontrada'})


@app.route('/config/limpiarDatos', methods=['GET'])
def limpiarDatos():
    listadoPizzas.clear()
    listadoUsuarios.clear()
    return jsonify({'message': 'Datos limpiados'})

@app.route('/config/leerDiccionario', methods=['POST'])
def postConfiguracion():
    data = request.get_data()
    root = ET.fromstring(data)

    # Leyendo pos.
    for palabra in root.find('sentimientos_positivos'):
        listadoPositivas.append(palabra.text.strip())

    # Leyendo neg.
    for palabra in root.find('sentimientos_negativos'):
        listadoNegativas.append(palabra.text.strip())

    # empresas:
    for empresa in root.find('empresas_analizar'):
        nombreE = empresa.find('nombre').text.strip().lower()
        empresaObj = Empresa(nombreE)
        print(nombreE)
        #servicios
        servicios = empresa.find('servicios')
        for servicio in servicios.findall('servicio'):
            nombreS = servicio.get('nombre').strip().lower()

            servicioObj = Servicio(nombreS)

            # alias:
            for alias in servicio.findall('alias'):
                servicioObj.alias.append(alias.text.strip().lower())

            empresaObj.servicios.append(servicioObj)


        listadoEmpresas.append(empresaObj)

    
    return jsonify({
        'mensaje': 'si se guardó todo',
        'positivas': listadoPositivas,
        'negativas': listadoNegativas,
        'empresas': [empresa.to_dict() for empresa in listadoEmpresas]
    }), 200
    

@app.route('/analisis/analizarMU', methods=['POST'])
def analizarMU():
    data = request.get_data()
    root = ET.fromstring(data)


    
    mensaje_texto = root.text.strip()
    
    fecha = re.search(r'(\d{2}/\d{2}/\d{4})', mensaje_texto).group(1)
    usuario = re.search(r'Usuario: ([^\s]+)', mensaje_texto).group(1)
    red_social = re.search(r'Red social: ([^\s]+)', mensaje_texto).group(1)



    palabras = re.findall(r'\b\w+\b', mensaje_texto.lower())
    contador_positivas = sum(1 for palabra in palabras if palabra in listadoPositivas)
    contador_negativas = sum(1 for palabra in palabras if palabra in listadoNegativas)


    total_palabras = contador_positivas + contador_negativas
    sentimiento_positivo = (contador_positivas / total_palabras * 100) if total_palabras > 0 else 0
    sentimiento_negativo = (contador_negativas / total_palabras * 100) if total_palabras > 0 else 0

    sentimiento_analizado = "neutro"

    if sentimiento_positivo > sentimiento_negativo:
        sentimiento_analizado = 'positivo'
    elif sentimiento_positivo == sentimiento_negativo:
        sentimiento_analizado = 'neutro'
    else:
        sentimiento_analizado = 'negativo'
    # Generar respuesta XML:
    respuesta = ET.Element("respuesta")
    ET.SubElement(respuesta, "fecha").text = fecha
    ET.SubElement(respuesta, "red_social").text = red_social
    ET.SubElement(respuesta, "usuario").text = usuario

    empresas = ET.SubElement(respuesta, "empresas")
    '''
     1. Ver qué empresas se encuentran en el listado de palabras obtenido del mensaje
     2. Ver qué alias se encuentra del servicio de la empresa encontrada en el mensaje
     3. ponerlo como salida del XML
    '''

    for empresa in listadoEmpresas:
        if empresa.nombre in palabras:
            empresa_elem = ET.SubElement(empresas, "empresa", nombre=empresa.nombre)
            for servicio in empresa.servicios:
                if servicio.nombre in palabras or any(alias in palabras for alias in servicio.alias):
                    ET.SubElement(empresa_elem, "servicio").text = servicio.nombre

    ET.SubElement(respuesta, "palabras_positivas").text = str(contador_positivas)
    ET.SubElement(respuesta, "palabras_negativas").text = str(contador_negativas)
    ET.SubElement(respuesta, "sentimiento_positivo").text = f"{sentimiento_positivo:.2f}%"
    ET.SubElement(respuesta, "sentimiento_negativo").text = f"{sentimiento_negativo:.2f}%"
    ET.SubElement(respuesta, "sentimiento_analizado").text = sentimiento_analizado

    # Convertir a XML
    respuesta_xml = ET.tostring(respuesta, encoding='UTF-8')

    # minidom:
    respuesta_xml = minidom.parseString(respuesta_xml).toprettyxml()

    #print(respuesta_xml)

    return respuesta_xml, 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)