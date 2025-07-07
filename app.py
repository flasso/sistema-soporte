from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporte@cloudsoftware.com.co'
app.config['MAIL_PASSWORD'] = 'TU_CONTRASEÑA_AQUÍ'
app.config['MAIL_DEFAULT_SENDER'] = 'soporte@cloudsoftware.com.co'
mail = Mail(app)

# Conexión a la base de datos
DB_URL = os.getenv("DATABASE_URL", "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db")

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def ensure_columns():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='incidentes' AND column_name='respuesta') THEN
                    ALTER TABLE incidentes ADD COLUMN respuesta TEXT;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='incidentes' AND column_name='archivo_respuesta') THEN
                    ALTER TABLE incidentes ADD COLUMN archivo_respuesta VARCHAR;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='incidentes' AND column_name='tiempo_respuesta') THEN
                    ALTER TABLE incidentes ADD COLUMN tiempo_respuesta INTERVAL;
                END IF;
            END$$;
        """)
        conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def soporte():
    conn = get_conn()
    if request.method == "POST":
        data = request.form
        archivo = request.files.get("archivo")
        archivo_nombre = archivo.filename if archivo else None

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO incidentes
                (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['nombre'], data['correo'], data['telefono'], data['empresa'],
                data['tipo_problema'], data['descripcion'], archivo_nombre,
                datetime.now(), 'pendiente'
            ))
            conn.commit()

        # Enviar correo de confirmación
        msg = Message("Incidente recibido",
                      recipients=[data['correo']],
                      body=f"Gracias {data['nombre']}, hemos recibido tu incidente y lo atenderemos pronto.")
        mail.send(msg)

        return redirect(url_for("gracias"))

    empresas = [
        'Seleccione una empresa',
        'Acomedios', 'Aldas','Adela', 'Asoredes', 'Big Media', 'Cafam', 'Century',
        'CNM', 'Contructora de Marcas', 'Dortiz', 'Elite', 'Factorial', 'Grupo One',
        'Zelva', 'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe',
        'Maproges', 'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens',
        'OMV', 'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
    ]
    return render_template("formulario.html", empresas=empresas)

@app.route("/gracias")
def gracias():
    return "Gracias por reportar tu incidente. Pronto nos pondremos en contacto."

@app.route("/admin")
def admin():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
        incidentes = cur.fetchall()
    return render_template("admin.html", incidentes=incidentes)

if __name__ == "__main__":
    ensure_columns()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
