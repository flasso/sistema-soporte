from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configuración correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'vrti crrt nkoa lonl'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

mail = Mail(app)

DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def now_colombia():
    tz = pytz.timezone('America/Bogota')
    return datetime.now(tz)

def get_conn():
    conn = psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)
    return conn

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS incidentes (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            correo TEXT,
            telefono TEXT,
            empresa TEXT,
            tipo_problema TEXT,
            descripcion TEXT,
            archivo TEXT,
            fecha_reporte TIMESTAMPTZ,
            estado TEXT,
            respuesta TEXT,
            archivo_respuesta TEXT,
            fecha_respuesta TIMESTAMPTZ
        );
        """)
        conn.commit()

init_db()

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        tipo_problema = request.form['tipo_problema']
        descripcion = request.form['descripcion']
        fecha_reporte = now_colombia()
        estado = 'pendiente'

        archivo = request.files.get('archivo')
        archivo_nombre = None
        if archivo and archivo.filename:
            archivo_nombre = f"{datetime.now().timestamp()}_{archivo.filename}"
            archivo.save(os.path.join(UPLOAD_FOLDER, archivo_nombre))

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte, estado))
            conn.commit()

        msg = Message('Nuevo incidente reportado', recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f"""Nuevo incidente:
Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo: {tipo_problema}
Descripción: {descripcion}"""
        mail.send(msg)

        return redirect('/gracias')

    empresas = [
        '', 'Acomedios', 'Aldas', 'Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
        'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One', 'Zelva', 
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges', 
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV', 
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    tipos_problema = ['Caso', 'Solicitud', 'Mejora']
    return render_template('formulario.html', empresas=empresas, tipos_problema=tipos_problema)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin')
def admin():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
        incidentes = cur.fetchall()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/responder/<int:incidente_id>', methods=['GET', 'POST'])
def responder(incidente_id):
    with get_conn() as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            respuesta = request.form['respuesta']
            estado = 'cerrado'
            fecha_respuesta = now_colombia()
            archivo = request.files.get('archivo_respuesta')
            archivo_nombre = None
            if archivo and archivo.filename:
                archivo_nombre = f"respuesta_{datetime.now().timestamp()}_{archivo.filename}"
                archivo.save(os.path.join(UPLOAD_FOLDER, archivo_nombre))

            cur.execute("""
                UPDATE incidentes
                SET respuesta = %s, archivo_respuesta = %s, fecha_respuesta = %s, estado = %s
                WHERE id = %s
            """, (respuesta, archivo_nombre, fecha_respuesta, estado, incidente_id))

            cur.execute("SELECT correo FROM incidentes WHERE id = %s", (incidente_id,))
            cliente = cur.fetchone()
            conn.commit()

            msg = Message('Respuesta a su incidente', recipients=[cliente['correo']])
            msg.body = f"""Su incidente ha sido respondido:
Respuesta: {respuesta}"""
            mail.send(msg)

            return redirect('/admin')

        cur.execute("SELECT * FROM incidentes WHERE id = %s", (incidente_id,))
        incidente = cur.fetchone()
    return render_template('responder.html', incidente=incidente)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
