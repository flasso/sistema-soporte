from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos PostgreSQL
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

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
        msg_soporte = Message(
            'Nuevo incidente reportado',
            recipients=['soporte@cloudsoftware.com.co'],
            sender='soporte@cloudsoftware.com.co'
        )
        msg_soporte.body = f"""Se ha reportado un nuevo incidente:

Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo de problema: {tipo_problema}
Descripción: {descripcion}
Fecha reporte: {fecha_reporte}
Estado: pendiente
"""
        mail.send(msg_soporte)

        # Enviar correo de confirmación al cliente
        msg_cliente = Message(
            'Tu incidente ha sido registrado',
            recipients=[correo],
            sender='soporte@cloudsoftware.com.co'
        )
        msg_cliente.body = f"""Hola {nombre},

Tu incidente ha sido registrado exitosamente. Nuestro equipo de soporte te contactará pronto.

Gracias por tu reporte.
"""
        mail.send(msg_cliente)

        return redirect('/gracias')
    
    empresas = [
        '', 'Acomedios', 'Aldas','Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
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
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
