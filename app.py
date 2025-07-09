from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# Configuración de base de datos
DB_URL = os.getenv("DB_URL", "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db")

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
        archivo = request.files.get('archivo')
        archivo_nombre = archivo.filename if archivo and archivo.filename else None

        fecha_colombia = datetime.now(timezone(timedelta(hours=-5))).isoformat()
        estado = 'pendiente'

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, fecha_colombia, estado))
        conn.commit()
        cur.close()
        conn.close()

        # Enviar correo a soporte
        msg = Message("Nuevo incidente reportado",
                      sender="soporte@cloudsoftware.com.co",
                      recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""
Nuevo incidente reportado:
Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Empresa: {empresa}
Tipo de problema: {tipo_problema}
Descripción: {descripcion}
Archivo: {archivo_nombre or 'N/A'}
Fecha: {fecha_colombia}
        """
        mail.send(msg)

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
        archivo = request.files.get('archivo')
        archivo_nombre = archivo.filename if archivo and archivo.filename else None

        fecha_respuesta = datetime.now(timezone(timedelta(hours=-5))).isoformat()

        cur.execute("""
            UPDATE incidentes
            SET respuesta = %s, archivo_respuesta = %s, fecha_respuesta = %s, estado = 'cerrado'
            WHERE id = %s;
        """, (respuesta, archivo_nombre, fecha_respuesta, id))
        conn.commit()

        # Obtener correo del cliente para avisarle
        cur.execute("SELECT correo FROM incidentes WHERE id = %s;", (id,))
        cliente = cur.fetchone()
        if cliente:
            msg = Message("Respuesta a tu incidente",
                          sender="soporte@cloudsoftware.com.co",
                          recipients=[cliente['correo']])
            msg.body = f"Tu incidente ha sido respondido:\n\n{respuesta}"
            mail.send(msg)

        cur.close()
        conn.close()
        return redirect(url_for('admin'))

    cur.execute("SELECT * FROM incidentes WHERE id = %s;", (id,))
    incidente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('responder.html', incidente=incidente)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
