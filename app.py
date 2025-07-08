from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.secret_key = 'secret-key'  # para mensajes flash
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Config DB
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

# Config Mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='soporte@cloudsoftware.com.co',
    MAIL_PASSWORD='yqwm byqv lkft suvx'
)
mail = Mail(app)

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
        fecha_reporte = datetime.now().isoformat()
        estado = 'pendiente'
        archivo_path = None

        archivo = request.files.get('archivo')
        if archivo and archivo.filename:
            archivo_path = os.path.join(UPLOAD_FOLDER, archivo.filename)
            archivo.save(archivo_path)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_path, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        # enviar correo
        msg = Message('Nuevo incidente reportado', recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f'Cliente: {nombre}\nEmpresa: {empresa}\nCorreo: {correo}\nTelefono: {telefono}\nTipo: {tipo_problema}\nDescripcion: {descripcion}'
        mail.send(msg)

        msg_cliente = Message('Tu incidente ha sido registrado', recipients=[correo])
        msg_cliente.body = 'Gracias por reportar tu incidente. Lo estamos revisando.'
        mail.send(msg_cliente)

        return redirect(url_for('gracias'))
    
    empresas = [
        '', 'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
        'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial', 'Grupo One', 'Zelva', 
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges', 
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV', 
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == 'POST':
        respuesta = request.form['respuesta']
        incidente_id = request.form['incidente_id']
        archivo_resp = request.files.get('archivo_resp')
        archivo_resp_path = None
        fecha_respuesta = datetime.now().isoformat()

        if archivo_resp and archivo_resp.filename:
            archivo_resp_path = os.path.join(UPLOAD_FOLDER, archivo_resp.filename)
            archivo_resp.save(archivo_resp_path)

        cur.execute("""
            UPDATE incidentes SET estado='cerrado', respuesta=%s, archivo_respuesta=%s, fecha_respuesta=%s WHERE id=%s
        """, (respuesta, archivo_resp_path, fecha_respuesta, incidente_id))
        conn.commit()

        cur.execute("SELECT correo FROM incidentes WHERE id=%s", (incidente_id,))
        correo_cliente = cur.fetchone()['correo']

        msg_cliente = Message('Tu incidente ha sido respondido', recipients=[correo_cliente])
        msg_cliente.body = f'Respuesta: {respuesta}'
        if archivo_resp_path:
            with app.open_resource(archivo_resp_path) as f:
                msg_cliente.attach(archivo_resp.filename, 'application/octet-stream', f.read())
        mail.send(msg_cliente)

        flash('Respuesta enviada y caso cerrado.')

    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
