from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Config Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
mail = Mail(app)

DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def colombia_now():
    tz = pytz.timezone('America/Bogota')
    return datetime.now(tz)

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
        archivo_nombre = None
        if archivo and archivo.filename:
            archivo_nombre = f"{colombia_now().timestamp()}_{archivo.filename}"
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))

        fecha_reporte = colombia_now()
        estado = 'pendiente'

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        msg = Message("Incidente recibido",
                      sender='soporte@cloudsoftware.com.co',
                      recipients=[correo])
        msg.body = "Tu incidente ha sido recibido. Nos pondremos en contacto pronto."
        mail.send(msg)

        return redirect('/gracias')

    empresas = ['', 'Acomedios', 'Aldas', 'Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM',
                'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One', 'Zelva',
                'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
                'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
                'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA']
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin')
def admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/responder/<int:incidente_id>', methods=['GET', 'POST'])
def responder(incidente_id):
    conn = get_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        archivo_resp = request.files['archivo_respuesta']
        archivo_resp_nombre = None
        if archivo_resp and archivo_resp.filename:
            archivo_resp_nombre = f"respuesta_{colombia_now().timestamp()}_{archivo_resp.filename}"
            archivo_resp.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_resp_nombre))

        fecha_respuesta = colombia_now()
        estado = 'cerrado'

        cur.execute("SELECT correo FROM incidentes WHERE id = %s", (incidente_id,))
        cliente = cur.fetchone()
        correo_cliente = cliente['correo'] if cliente else None

        cur.execute("""
            UPDATE incidentes
            SET respuesta = %s, archivo_respuesta = %s, fecha_respuesta = %s, estado = %s
            WHERE id = %s
        """, (respuesta, archivo_resp_nombre, fecha_respuesta, estado, incidente_id))
        conn.commit()

        if correo_cliente:
            msg = Message("Respuesta a tu incidente",
                          sender='soporte@cloudsoftware.com.co',
                          recipients=[correo_cliente])
            msg.body = respuesta
            if archivo_resp_nombre:
                msg.attach(archivo_resp_nombre, "application/octet-stream",
                           open(os.path.join(app.config['UPLOAD_FOLDER'], archivo_resp_nombre), 'rb').read())
            mail.send(msg)

        cur.close()
        conn.close()
        return redirect(url_for('admin'))

    cur.execute("SELECT * FROM incidentes WHERE id = %s", (incidente_id,))
    incidente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('responder.html', incidente=incidente)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
