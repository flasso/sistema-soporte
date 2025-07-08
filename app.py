from flask import Flask, render_template, request, redirect, send_from_directory, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configura tu correo
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='soporte@cloudsoftware.com.co',
    MAIL_PASSWORD='yqwm byqv lkft suvx',
    MAIL_DEFAULT_SENDER='soporte@cloudsoftware.com.co'
)
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
        archivo = request.files['archivo']
        fecha_reporte = datetime.now()
        estado = 'pendiente'

        archivo_nombre = None
        if archivo and archivo.filename:
            archivo_nombre = f"{datetime.now().timestamp()}_{archivo.filename}"
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        # Correo a soporte
        msg_soporte = Message(f"Nuevo incidente de {nombre}",
                              recipients=['soporte@cloudsoftware.com.co'])
        msg_soporte.body = f"""Incidente reportado por {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo: {tipo_problema}
Descripción: {descripcion}
"""
        if archivo_nombre:
            msg_soporte.attach(archivo_nombre, "application/octet-stream",
                               open(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre), 'rb').read())
        mail.send(msg_soporte)

        # Correo al cliente
        msg_cliente = Message("Hemos recibido tu incidente",
                              recipients=[correo])
        msg_cliente.body = f"""Hola {nombre},

Hemos recibido tu solicitud y la estamos revisando.

Gracias,
Soporte Cloud Software
"""
        mail.send(msg_cliente)

        return redirect('/gracias')
    
    empresas = [
        '', 'Acomedios', 'Aldas', 'Adela','Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
        'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One', 'Zelva', 
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges', 
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV', 
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == 'POST':
        incidente_id = request.form['incidente_id']
        respuesta = request.form['respuesta']
        archivo_resp = request.files['archivo_respuesta']
        fecha_respuesta = datetime.now()
        estado = 'cerrado'

        archivo_resp_nombre = None
        if archivo_resp and archivo_resp.filename:
            archivo_resp_nombre = f"respuesta_{datetime.now().timestamp()}_{archivo_resp.filename}"
            archivo_resp.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_resp_nombre))

        # Obtener correo del cliente
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
                          recipients=[correo_cliente])
            msg.body = f"""Hola,

Hemos respondido a tu incidente:

{respuesta}

Gracias,
Soporte Cloud Software
"""
            if archivo_resp_nombre:
                msg.attach(archivo_resp_nombre, "application/octet-stream",
                           open(os.path.join(app.config['UPLOAD_FOLDER'], archivo_resp_nombre), 'rb').read())
            mail.send(msg)

    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
