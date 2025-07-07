from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configuración de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'tu_clave_aqui'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

mail = Mail(app)

# URL de conexión PostgreSQL desde Render
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Crear tabla incidentes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidentes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            correo VARCHAR(100) NOT NULL,
            telefono VARCHAR(20) NOT NULL,
            empresa VARCHAR(100) NOT NULL,
            tipo_problema VARCHAR(50) NOT NULL,
            descripcion TEXT NOT NULL,
            archivo VARCHAR(200),
            fecha_reporte TIMESTAMPTZ NOT NULL,
            estado VARCHAR(20) DEFAULT 'pendiente',
            fecha_resolucion TIMESTAMPTZ
        )
    """)
    # Crear tabla clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE
        )
    """)
    # Insertar empresas si no existen
    empresas = [
        'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam',
        'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
        'Elite', 'Factorial', 'Grupo One', 'Zelva',
        'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
        'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
        'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    for empresa in empresas:
        cur.execute("""
            INSERT INTO clientes (nombre) VALUES (%s)
            ON CONFLICT (nombre) DO NOTHING
        """, (empresa,))
    conn.commit()
    cur.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def soporte():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        tipo_problema = request.form["tipo_problema"]
        descripcion = request.form["descripcion"]
        archivo = request.files.get("archivo")
        archivo_nombre = archivo.filename if archivo else None

        now = datetime.now(pytz.timezone("America/Bogota"))
        cur.execute("""
            INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo_nombre, now))
        conn.commit()

        # Enviar correo opcional
        msg = Message("Nuevo incidente reportado", recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"Incidente reportado por {nombre} ({correo})\nEmpresa: {empresa}\nTel: {telefono}\nTipo: {tipo_problema}\nDescripción:\n{descripcion}"
        mail.send(msg)

        cur.close()
        conn.close()
        return redirect(url_for("gracias"))

    # GET
    cur.execute("SELECT nombre FROM clientes ORDER BY nombre")
    empresas = [row['nombre'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template("formulario.html", empresas=empresas)

@app.route("/gracias")
def gracias():
    return "Gracias por reportar el incidente."

@app.route("/admin")
def admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
    incidentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin.html", incidentes=incidentes)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
