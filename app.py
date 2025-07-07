from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configuración base de datos
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

# Configuración correo
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='soporte@cloudsoftware.com.co',
    MAIL_PASSWORD='tu_contraseña_aquí',
    MAIL_DEFAULT_SENDER='soporte@cloudsoftware.com.co'
)
mail = Mail(app)

# Lista fija de empresas
EMPRESAS = [
    'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM',
    'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial', 'Grupo One',
    'Zelva', 'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe',
    'Maproges', 'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens',
    'OMV', 'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
]

@app.route("/", methods=["GET", "POST"])
def soporte():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        tipo_problema = request.form["tipo_problema"]
        descripcion = request.form["descripcion"]

        tz = pytz.timezone('America/Bogota')
        fecha = datetime.now(tz)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes
            (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha, 'pendiente'))
        conn.commit()
        cur.close()
        conn.close()

        msg = Message("Nuevo incidente reportado",
                      recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""
        Nombre: {nombre}
        Correo: {correo}
        Teléfono: {telefono}
        Empresa: {empresa}
        Tipo de problema: {tipo_problema}
        Descripción: {descripcion}
        Fecha: {fecha}
        """
        mail.send(msg)

        return redirect(url_for("gracias"))

    return render_template("index.html", empresas=EMPRESAS)

@app.route("/gracias")
def gracias():
    return "Gracias por reportar tu incidente. Nos pondremos en contacto."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
