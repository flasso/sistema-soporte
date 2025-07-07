from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from psycopg2.extras import RealDictCursor
import psycopg2
from datetime import datetime
import pytz

app = Flask(__name__)

# Configuración de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'tu_contraseña_aqui'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

mail = Mail(app)

# URL completa de conexión a PostgreSQL
DB_URL = 'postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db'

empresas = [
    'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam',
    'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
    'Elite', 'Factorial', 'Grupo One', 'Zelva',
    'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
    'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
    'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
]

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
        archivo = request.files.get('archivo')

        tz = pytz.timezone('America/Bogota')
        fecha_reporte = datetime.now(tz)

        archivo_nombre = None
        if archivo and archivo.filename:
            archivo_nombre = archivo.filename
            archivo.save(f'static/uploads/{archivo_nombre}')

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_reporte))
        conn.commit()
        cur.close()
        conn.close()

        msg = Message(f'Nuevo incidente de {nombre}', recipients=['soporte@cloudsoftware.com.co'])
        msg.body = f"""Se ha reportado un nuevo incidente:
Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo: {tipo_problema}
Descripción: {descripcion}
"""
        mail.send(msg)

        return redirect(url_for('gracias'))

    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return "¡Gracias por reportar el incidente! Lo revisaremos pronto."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
