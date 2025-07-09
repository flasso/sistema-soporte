from flask import Flask, render_template, request, redirect, send_from_directory
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'
mail = Mail(app)

DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def ensure_columns():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='incidentes' AND column_name='respuesta') THEN
                ALTER TABLE incidentes ADD COLUMN respuesta TEXT;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='incidentes' AND column_name='archivo_respuesta') THEN
                ALTER TABLE incidentes ADD COLUMN archivo_respuesta TEXT;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='incidentes' AND column_name='fecha_respuesta') THEN
                ALTER TABLE incidentes ADD COLUMN fecha_respuesta TIMESTAMPTZ;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='incidentes' AND column_name='estado') THEN
                ALTER TABLE incidentes ADD COLUMN estado VARCHAR(50) DEFAULT 'pendiente';
            END IF;
        END
        $$;
    """)
    conn.commit()
    cur.close()
    conn.close()

ensure_columns()

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        tipo_problema = request.form['tipo_problema']
        descripcion = request.form['descripcion']
        archivo = request.files.get('archivo')
        archivo_nombre = None
        if archivo and archivo.filename:
            archivo_nombre = archivo.filename
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))
        fecha_reporte = datetime.now() - timedelta(hours=5)
        estado = 'pendiente'

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        # Enviar correo al cliente
        msg_cliente = Message(f"Incidente recibido - {empresa}",
                              recipients=[correo])
        msg_cliente.body = f"Hemos recibido su incidente: {descripcion}"
        mail.send(msg_cliente)

        # Enviar correo al soporte
        msg_soporte = Message(f"Nuevo incidente - {empresa}",
                              recipients=[app.config['MAIL_USERNAME']])
        msg_soporte.body = f"Nuevo incidente:\n\n{descripcion}"
        mail.send(msg_soporte)

        return redirect('/gracias')
    
    empresas = [
        '', 'Acomedios', 'Aldas', 'Adela','Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
        'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One', 'Zelva', 
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges', 
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV', 
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    tipos_problema = ['bug', 'soporte', 'sugerencia']
    return render_template('formulario.html', empresas=empresas, tipos_problema=tipos_problema)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
def admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/responder/<int:incidente_id>', methods=['GET', 'POST'])
def responder(incidente_id):
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        archivo_respuesta = request.files.get('archivo_respuesta')
        archivo_nombre = None
        if archivo_respuesta and archivo_respuesta.filename:
            archivo_nombre = archivo_respuesta.filename
            archivo_respuesta.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))
        fecha_respuesta = datetime.now() - timedelta(hours=5)
        estado = 'cerrado'

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE incidentes
            SET respuesta = %s, archivo_respuesta = %s, fecha_respuesta = %s, estado = %s
            WHERE id = %s
        """, (respuesta, archivo_nombre, fecha_respuesta, estado, incidente_id))
        conn.commit()

        # Obtener correo del cliente
        cur.execute("SELECT correo FROM incidentes WHERE id = %s", (incidente_id,))
        cliente = cur.fetchone()
        if cliente:
            msg = Message(f"Respuesta a su incidente #{incidente_id}",
                          recipients=[cliente['correo']])
            msg.body = respuesta
            mail.send(msg)

        cur.close()
        conn.close()
        return redirect('/admin')
    
    # Mostrar formulario de respuesta
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes WHERE id = %s", (incidente_id,))
    incidente = cur.fetchone()
    cur.close()
    conn.close()
    if not incidente:
        return "Incidente no encontrado", 404
    return render_template('responder.html', incidente=incidente)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
