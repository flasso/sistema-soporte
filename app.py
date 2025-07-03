from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'
mail = Mail(app)

# Carpeta de archivos
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB = 'incidentes.db'

def crear_tabla():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        correo TEXT,
        telefono TEXT,
        empresa TEXT,
        fecha TEXT,
        tipo_problema TEXT,
        descripcion TEXT,
        archivo TEXT DEFAULT '',
        respuesta TEXT DEFAULT '',
        archivo_respuesta TEXT DEFAULT '',
        estado TEXT DEFAULT 'Abierto'
    )''')
    conn.commit()
    conn.close()

def crear_tabla_empresas():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    )''')
    conn.commit()
    conn.close()

def insertar_empresas_iniciales():
    empresas = [
         'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam',
        'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
        'Elite', 'Factorial', 'Grupo One', 'Zelva',
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for empresa in empresas:
        try:
            c.execute("INSERT INTO empresas (nombre) VALUES (?)", (empresa,))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def agregar_columna_fecha_respuesta():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE incidentes ADD COLUMN fecha_respuesta TEXT")
        print("Columna fecha_respuesta agregada.")
    except sqlite3.OperationalError:
        print("La columna fecha_respuesta ya existe.")
    conn.commit()
    conn.close()

crear_tabla()
crear_tabla_empresas()
insertar_empresas_iniciales()
agregar_columna_fecha_respuesta()

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        descripcion = request.form['descripcion']
        tipo_problema = request.form['tipo_problema']
        archivo = request.files.get('archivo')
        archivo_nombre = ''

        if archivo and archivo.filename:
            archivo_nombre = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}"
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))

        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO incidentes (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion, archivo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion, archivo_nombre))
        conn.commit()
        conn.close()

        msg = Message("Nuevo incidente de soporte",
                      recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""
        Nuevo incidente:
        Nombre: {nombre}
        Correo: {correo}
        Teléfono: {telefono}
        Empresa: {empresa}
        Tipo de problema: {tipo_problema}
        Descripción: {descripcion}
        Fecha: {fecha}
        """
        if archivo_nombre:
            with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre)) as fp:
                msg.attach(archivo_nombre, archivo.content_type, fp.read())

        mail.send(msg)

        return redirect(url_for('gracias'))

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT nombre FROM empresas ORDER BY nombre ASC")
    empresas = [fila[0] for fila in c.fetchall()]
    conn.close()
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return "Gracias por enviar tu incidente. Nuestro equipo lo atenderá pronto."

@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM incidentes ORDER BY fecha DESC")
    incidentes = c.fetchall()
    conn.close()

    pendientes = sum(1 for i in incidentes if i['estado'] == 'Abierto')
    cerrados = sum(1 for i in incidentes if i['estado'] == 'Cerrado')

    for incidente in incidentes:
        if incidente['estado'] == 'Cerrado' and incidente['fecha_respuesta']:
            inicio = datetime.strptime(incidente['fecha'], '%Y-%m-%d %H:%M:%S')
            fin = datetime.strptime(incidente['fecha_respuesta'], '%Y-%m-%d %H:%M:%S')
            diff = fin - inicio
            horas = diff.total_seconds() / 3600
            incidente['tiempo_resolucion'] = f"{horas:.1f} horas"
        else:
            incidente['tiempo_resolucion'] = '-'

    return render_template('admin.html', incidentes=incidentes, pendientes=pendientes, cerrados=cerrados)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/responder/<int:id>', methods=['POST'])
def responder(id):
    respuesta = request.form['respuesta']
    archivo_respuesta = request.files.get('archivo_respuesta')
    archivo_respuesta_nombre = ''

    if archivo_respuesta and archivo_respuesta.filename:
        archivo_respuesta_nombre = f"respuesta_{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo_respuesta.filename}"
        archivo_respuesta.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_respuesta_nombre))

    fecha_respuesta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE incidentes SET respuesta = ?, estado = ?, archivo_respuesta = ?, fecha_respuesta = ? WHERE id = ?",
              (respuesta, 'Cerrado', archivo_respuesta_nombre, fecha_respuesta, id))
    c.execute("SELECT correo FROM incidentes WHERE id = ?", (id,))
    correo_cliente = c.fetchone()[0]
    conn.commit()
    conn.close()

    msg = Message("Respuesta a tu incidente",
                  recipients=[correo_cliente])
    msg.body = f"Hola, esta es la respuesta a tu incidente:\n\n{respuesta}\n\nGracias por contactarnos."
    if archivo_respuesta_nombre:
        with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'], archivo_respuesta_nombre)) as fp:
            msg.attach(archivo_respuesta_nombre, archivo_respuesta.content_type, fp.read())

    mail.send(msg)

    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
