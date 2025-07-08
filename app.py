from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# PostgreSQL
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

# Configuración correo
app.config['MAIL_SERVER'] = 'smtp.tucorreo.com'  # cámbialo a tu SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'  # tu cuenta
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'            # tu contraseña
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

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
        return redirect('/gracias')
    
    empresas = [
        '', 'Acomedios', 'Aldas', 'Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM', 
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
        incidente_id = request.form['incidente_id']
        respuesta = request.form['respuesta']
        fecha_respuesta = datetime.now().isoformat()
        # actualiza y obtiene correo del cliente
        cur.execute("""
            UPDATE incidentes 
            SET respuesta=%s, fecha_respuesta=%s, estado='cerrado'
            WHERE id=%s
            RETURNING correo, nombre;
        """, (respuesta, fecha_respuesta, incidente_id))
        result = cur.fetchone()
        conn.commit()

        # enviar correo
        if result:
            msg = Message("Respuesta a tu incidente", recipients=[result['correo']])
            msg.body = f"Hola {result['nombre']},\n\nHemos respondido a tu incidente:\n\n{respuesta}\n\nGracias."
            mail.send(msg)

    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
