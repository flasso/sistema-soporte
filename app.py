from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configura correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

mail = Mail(app)

DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        tipo_problema = request.form['tipo_problema']
        descripcion = request.form['descripcion']
        estado = 'pendiente'

        archivo = request.files.get('archivo')
        archivo_nombre = archivo.filename if archivo else None

        fecha_reporte = datetime.now(pytz.timezone('America/Bogota')).isoformat()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        # Enviar correo a soporte
        msg = Message('Nuevo incidente reportado', recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f"""Se reportó un nuevo incidente:
        Nombre: {nombre}
        Correo: {correo}
        Teléfono: {telefono}
        Empresa: {empresa}
        Tipo: {tipo_problema}
        Descripción: {descripcion}
        """
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error enviando correo a soporte: {e}")

        return redirect('/gracias')

    empresas = [
        '', 'Acomedios', 'Aldas', 'Asoredes','Adela', 'Big Media', 'Cafam', 'Century', 'CNM',
        'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One', 'Zelva',
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin')
def admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
    incidentes = cur.fetchall()

    # Ajustar hora a Bogotá para mostrar
    for inc in incidentes:
        if inc['fecha_reporte']:
            inc['fecha_reporte'] = inc['fecha_reporte'].astimezone(pytz.timezone('America/Bogota'))
        if inc.get('fecha_respuesta'):
            inc['fecha_respuesta'] = inc['fecha_respuesta'].astimezone(pytz.timezone('America/Bogota'))

    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/responder/<int:incidente_id>', methods=['GET', 'POST'])
def responder(incidente_id):
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        archivo = request.files.get('archivo_respuesta')
        archivo_nombre = archivo.filename if archivo else None

        fecha_respuesta = datetime.now(pytz.timezone('America/Bogota')).isoformat()
        estado = 'cerrado'

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT correo FROM incidentes WHERE id = %s", (incidente_id,))
        cliente = cur.fetchone()

        if not cliente:
            conn.close()
            return "Error: incidente no encontrado", 404

        correo_cliente = cliente['correo']

        cur.execute("""
            UPDATE incidentes
            SET respuesta = %s, archivo_respuesta = %s, fecha_respuesta = %s, estado = %s
            WHERE id = %s
        """, (respuesta, archivo_nombre, fecha_respuesta, estado, incidente_id))
        conn.commit()
        cur.close()
        conn.close()

        # Enviar correo al cliente
        msg = Message('Respuesta a tu incidente', recipients=[correo_cliente, 'soporte@cloudsoftware.com.co'])
        msg.body = f"""Su incidente ha sido respondido:
        Respuesta: {respuesta}
        """
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error enviando correo al cliente: {e}")

        return redirect('/admin')

    return render_template('responder.html', incidente_id=incidente_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
