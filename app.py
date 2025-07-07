from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'Light@940402.'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'

mail = Mail(app)

# URL interna de Render para la base
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"
)

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS incidentes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    correo VARCHAR(100) NOT NULL,
                    telefono VARCHAR(50),
                    empresa VARCHAR(100),
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_problema VARCHAR(50),
                    descripcion TEXT,
                    estado VARCHAR(20) DEFAULT 'Abierto',
                    respuesta TEXT,
                    fecha_respuesta TIMESTAMP
                );
            """)
            # Insertar las empresas si aún no están
            cur.execute("SELECT COUNT(*) AS total FROM empresas;")
            if cur.fetchone()['total'] == 0:
                empresas = [
                    'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam',
                    'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ',
                    'Elite', 'Factorial', 'Grupo One', 'Zelva',
                    'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
                    'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
                    'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
                ]
                for e in empresas:
                    cur.execute("INSERT INTO empresas (nombre) VALUES (%s) ON CONFLICT DO NOTHING;", (e,))
        conn.commit()

@app.route("/", methods=["GET", "POST"])
def soporte():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nombre FROM empresas ORDER BY nombre;")
            empresas = [row['nombre'] for row in cur.fetchall()]

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        tipo_problema = request.form["tipo_problema"]
        descripcion = request.form["descripcion"]
        fecha = datetime.now(pytz.timezone('America/Bogota'))

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO incidentes (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (nombre, correo, telefono, empresa, fecha, tipo_problema, descripcion))
            conn.commit()

        msg = Message("Nuevo incidente recibido", recipients=["soporte@cloudsoftware.com.co"])
        msg.body = f"""
        Se ha recibido un nuevo incidente de {nombre} ({correo}):

        Empresa: {empresa}
        Teléfono: {telefono}
        Tipo: {tipo_problema}
        Descripción: {descripcion}
        """
        mail.send(msg)

        return redirect(url_for("gracias"))

    return render_template("formulario.html", empresas=empresas)

@app.route("/gracias")
def gracias():
    return "<h2>Gracias por reportar tu incidente. Pronto nos pondremos en contacto.</h2>"

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
