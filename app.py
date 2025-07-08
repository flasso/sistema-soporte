from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'
mail = Mail(app)

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

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado))
        conn.commit()
        cur.close()
        conn.close()

        # Enviar correo a soporte
        msg = Message('Nuevo incidente reportado',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f"""Se ha reportado un nuevo incidente:

Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo de problema: {tipo_problema}
Descripción: {descripcion}
"""
        mail.send(msg)

        # Enviar correo al cliente
        msg_cliente = Message('Hemos recibido tu incidente',
                              sender=app.config['MAIL_USERNAME'],
                              recipients=[correo])
        msg_cliente.body = "Gracias por reportar tu incidente. Nos pondremos en contacto contigo pronto."
        mail.send(msg_cliente)

        return redirect('/gracias')
    
    empresas = [
        '', 'Acomedios', 'Aldas', 'Aldea', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
        'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial', 'Grupo One', 'Zelva', 
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
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/responder/<int:id>', methods=['GET', 'POST'])
def responder(id):
    conn = get_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        cur.execute("""
            UPDATE incidentes 
            SET respuesta = %s, estado = 'cerrado', fecha_respuesta = NOW()
            WHERE id = %s;
        """, (respuesta, id))
        conn.commit()

        # Obtener datos del cliente para enviar correo
        cur.execute("SELECT correo FROM incidentes WHERE id = %s;", (id,))
        cliente = cur.fetchone()
        if cliente and cliente['correo']:
            msg_cliente = Message('Respuesta a tu incidente',
                                  sender=app.config['MAIL_USERNAME'],
                                  recipients=[cliente['correo']])
            msg_cliente.body = f"Respuesta a tu incidente: {respuesta}"
            mail.send(msg_cliente)

        cur.close()
        conn.close()
        return redirect('/admin')

    # GET: muestra formulario
    cur.execute("SELECT * FROM incidentes WHERE id = %s;", (id,))
    incidente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('responder.html', incidente=incidente)

@app.route('/cerrar/<int:id>')
def cerrar(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE incidentes 
        SET estado = 'cerrado', fecha_respuesta = NOW()
        WHERE id = %s;
    """, (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
