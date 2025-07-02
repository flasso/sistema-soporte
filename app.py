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
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'  # Cambia si es necesario
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'  # Usa una contraseña de aplicación
mail = Mail(app)

# Carpeta para archivos
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos
DB = 'incidentes.db'

def crear_tabla():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        correo TEXT,
        telefono TEXT,
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

crear_tabla()

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
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
        c.execute("INSERT INTO incidentes (nombre, correo, telefono, fecha, tipo_problema, descripcion, archivo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (nombre, correo, telefono, fecha, tipo_problema, descripcion, archivo_nombre))
        conn.commit()
        conn.close()

        # Enviar correo a soporte
        msg = Message("Nuevo incidente de soporte",
                      recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""
        Nuevo incidente:
        Nombre: {nombre}
        Correo: {correo}
        Teléfono: {telefono}
        Tipo de problema: {tipo_problema}
        Descripción: {descripcion}
        Fecha: {fecha}
        """
        if archivo_nombre:
            with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre)) as fp:
                msg.attach(archivo_nombre, archivo.content_type, fp.read())

        mail.send(msg)
        return redirect(url_for('gracias'))

    return render_template('formulario.html')

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
    return render_template('admin.html', incidentes=incidentes)

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

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE incidentes SET respuesta = ?, estado = ?, archivo_respuesta = ? WHERE id = ?", (respuesta, 'Cerrado', archivo_respuesta_nombre, id))
    c.execute("SELECT correo FROM incidentes WHERE id = ?", (id,))
    correo_cliente = c.fetchone()[0]
    conn.commit()
    conn.close()

    # Enviar correo con respuesta
    msg = Message("Respuesta a tu incidente", recipients=[correo_cliente])
    msg.body = f"Hola, esta es la respuesta a tu incidente:\n\n{respuesta}\n\nGracias por contactarnos."
    if archivo_respuesta_nombre:
        with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'], archivo_respuesta_nombre)) as fp:
            msg.attach(archivo_respuesta_nombre, archivo_respuesta.content_type, fp.read())

    mail.send(msg)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    crear_tabla()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

