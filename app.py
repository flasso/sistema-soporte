from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'
mail = Mail(app)

def hora_colombia():
    zona = pytz.timezone('America/Bogota')
    return datetime.now(zona).strftime('%Y-%m-%d %H:%M:%S')

DB_URL = os.environ.get('DATABASE_URL')

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

@app.route('/', methods=['GET', 'POST'])
def soporte():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        descripcion = request.form['descripcion']
        tipo_problema = request.form['tipo_problema']
        fecha = hora_colombia()

        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Abierto')
        """, (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion))
        conn.commit()

        msg = Message("Nuevo incidente de soporte", recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""Nuevo incidente:
Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo: {tipo_problema}
Descripción: {descripcion}
Fecha: {fecha}"""
        mail.send(msg)

        conn.close()
        return redirect(url_for('gracias'))

    cur.execute("SELECT nombre FROM empresas ORDER BY nombre ASC")
    empresas = [e['nombre'] for e in cur.fetchall()]
    conn.close()

    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return "Gracias por reportar tu incidente. Te responderemos pronto."

@app.route('/admin')
def admin():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM incidentes ORDER BY fecha DESC")
    rows = cur.fetchall()
    conn.close()

    incidentes = []
    pendientes = sum(1 for r in rows if r['estado'] == 'Abierto')
    cerrados = sum(1 for r in rows if r['estado'] != 'Abierto')

    for r in rows:
        if r['estado'] != 'Abierto' and r['fecha_respuesta']:
            inicio = datetime.strptime(r['fecha'], '%Y-%m-%d %H:%M:%S')
            fin = datetime.strptime(r['fecha_respuesta'], '%Y-%m-%d %H:%M:%S')
            diff = fin - inicio
            horas = diff.total_seconds() / 3600
            r['tiempo_resolucion'] = f"{horas:.1f} horas"
        else:
            r['tiempo_resolucion'] = '-'
        incidentes.append(r)

    return render_template('admin.html', incidentes=incidentes, pendientes=pendientes, cerrados=cerrados)

@app.route('/responder/<int:id>', methods=['POST'])
def responder(id):
    respuesta = request.form['respuesta']
    fecha_respuesta = hora_colombia()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("UPDATE incidentes SET respuesta=%s, estado='Cerrado', fecha_respuesta=%s WHERE id=%s",
                (respuesta, fecha_respuesta, id))
    conn.commit()

    cur.execute("SELECT correo FROM incidentes WHERE id=%s", (id,))
    correo_cliente = cur.fetchone()['correo']
    conn.close()

    msg = Message("Respuesta a tu incidente", recipients=[correo_cliente])
    msg.body = f"""Hola, esta es la respuesta a tu incidente:
{respuesta}
Gracias por contactarnos."""
    mail.send(msg)

    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
