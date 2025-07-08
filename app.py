from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Crear carpeta uploads si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configuración de correo
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='soporte@cloudsoftware.com.co',
    MAIL_PASSWORD='yqwm byqv lkft suvx',
    MAIL_DEFAULT_SENDER='soporte@cloudsoftware.com.co'
)

mail = Mail(app)

# Conexión a la BD
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

EMPRESAS = [
    'Acomedios', 'Aldas','Alde', 'Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
    'Elite', 'Factorial', 'Grupo One', 'Zelva', 'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
    'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV', 'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
]

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        tipo_problema = request.form['tipo_problema']
        descripcion = request.form['descripcion']
        archivo = request.files['archivo']
        filename = None

        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        fecha_reporte = datetime.now(pytz.timezone('America/Bogota'))

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, filename, fecha_reporte))
        conn.commit()
        cur.close()
        conn.close()

        msg = Message("Nuevo incidente recibido", recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f"Incidente de {nombre} ({correo}):\n\n{descripcion}"
        mail.send(msg)

        return render_template('gracias.html')

    return render_template('formulario.html', empresas=EMPRESAS)

@app.route('/admin')
def admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/contestar/<int:id>', methods=['GET', 'POST'])
def contestar(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes WHERE id = %s", (id,))
    incidente = cur.fetchone()

    if request.method == 'POST':
        respuesta = request.form['respuesta']
        archivo_respuesta = request.files['archivo_respuesta']
        archivo_respuesta_filename = None

        if archivo_respuesta and archivo_respuesta.filename != '':
            archivo_respuesta_filename = secure_filename(archivo_respuesta.filename)
            archivo_respuesta.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_respuesta_filename))

        fecha_cierre = datetime.now(pytz.timezone('America/Bogota'))
        tiempo_respuesta = fecha_cierre - incidente['fecha_reporte']

        cur.execute("""
            UPDATE incidentes
            SET respuesta = %s, archivo_respuesta = %s, estado = 'cerrado', tiempo_respuesta = %s
            WHERE id = %s
        """, (respuesta, archivo_respuesta_filename, str(tiempo_respuesta), id))
        conn.commit()

        msg = Message("Respuesta a tu incidente", recipients=[incidente['correo']])
        msg.body = f"Hola {incidente['nombre']},\n\nTu incidente ha sido respondido:\n\n{respuesta}\n\nGracias."
        mail.send(msg)

        cur.close()
        conn.close()
        return redirect(url_for('admin'))

    cur.close()
    conn.close()
    return render_template('contestar.html', incidente=incidente)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
