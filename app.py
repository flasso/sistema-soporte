from flask import Flask, render_template, request
from flask_mail import Mail, Message
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'  # 👉 Reemplaza con tu correo
app.config['MAIL_PASSWORD'] = 'yqwm byqv lkft suvx'  # 👉 Reemplaza con tu contraseña de aplicación
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'  # 👉 Debe ser el mismo correo

mail = Mail(app)

# Crear base de datos
def init_db():
    conn = sqlite3.connect("soporte.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            correo TEXT,
            descripcion TEXT,
            fecha_reporte TEXT,
            respuesta TEXT,
            fecha_respuesta TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        descripcion = request.form['descripcion']
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Guardar en base de datos
        conn = sqlite3.connect("soporte.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO incidentes (nombre, correo, descripcion, fecha_reporte) VALUES (?, ?, ?, ?)",
                       (nombre, correo, descripcion, fecha))
        conn.commit()
        conn.close()

        # Enviar correo
        msg = Message("📩 Nuevo incidente de soporte registrado",
                      recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""Se ha registrado un nuevo incidente de soporte:

Nombre: {nombre}
Correo: {correo}
Teléfono: {telefono}
Descripción: {descripcion}
Fecha de reporte: {fecha}
"""
        mail.send(msg)

        return "✅ Tu mensaje ha sido enviado correctamente. Gracias."

    return render_template('formulario.html')

@app.route('/admin')
def admin():
    conn = sqlite3.connect("soporte.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidentes")
    datos = cursor.fetchall()
    conn.close()
    return render_template("panel.html", datos=datos)

@app.route('/caso/<int:id>', methods=['GET', 'POST'])



@app.route('/caso/<int:id>', methods=['GET', 'POST'])
def detalle(id):
    conn = sqlite3.connect("soporte.db")
    cursor = conn.cursor()

    # Obtener el caso
    cursor.execute("SELECT * FROM incidentes WHERE id=?", (id,))
    caso = cursor.fetchone()

    if request.method == 'POST':
        respuesta = request.form['respuesta']
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Guardar la respuesta en la base de datos
        cursor.execute("UPDATE incidentes SET respuesta=?, fecha_respuesta=? WHERE id=?",
                       (respuesta, fecha, id))
        conn.commit()

        # Enviar correo al cliente con la respuesta
        correo_cliente = caso[2]  # índice del correo en la tupla
        nombre_cliente = caso[1]
        descripcion = caso[3]

        msg = Message("🛠️ Respuesta a tu solicitud de soporte",
                      recipients=[correo_cliente])
        msg.body = f"""Hola {nombre_cliente},

Hemos revisado tu caso registrado el {caso[4]} con la siguiente descripción:

"{descripcion}"

Nuestra respuesta es:

{respuesta}

Fecha de respuesta: {fecha}

Gracias por confiar en nuestro equipo de soporte.
"""
        mail.send(msg)

        # Volver a cargar el caso con los cambios
        cursor.execute("SELECT * FROM incidentes WHERE id=?", (id,))
        caso = cursor.fetchone()

    conn.close()
    return render_template("detalle.html", caso=caso)

if __name__ == '__main__':
    init_db()
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

