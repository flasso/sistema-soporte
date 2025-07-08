from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from psycopg2.extras import RealDictCursor
from datetime import datetime
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuración de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'TU_PASSWORD_GMAIL'
mail = Mail(app)

# Variable de entorno para la DB
DB_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/formulario')
def formulario():
    empresas = [
        'Seleccione una empresa',
        'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam',
        'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
        'Elite', 'Factorial', 'Grupo One', 'Zelva', 'Integracion',
        'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens',
        'OMV', 'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    return render_template('formulario.html', empresas=empresas)

@app.route('/enviar', methods=['POST'])
def enviar():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    empresa = request.form['empresa']
    tipo = request.form['tipo_problema']
    descripcion = request.form['descripcion']
    fecha_reporte = datetime.now().isoformat()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO incidentes
                (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pendiente')
            """, (nombre, correo, telefono, empresa, tipo, descripcion, fecha_reporte))
            conn.commit()

    # Enviar correo al cliente
    msg = Message(f"Incidente recibido: {tipo}",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[correo])
    msg.body = f"""
Hola {nombre},

Hemos recibido tu incidente con la siguiente descripción:
"{descripcion}"

Pronto te contactaremos con una respuesta.

Gracias,
Equipo de Soporte
"""
    mail.send(msg)

    return render_template('gracias.html')

@app.route('/admin')
def admin():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
            incidentes = cur.fetchall()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
