from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)

DB_URL = os.getenv("DATABASE_URL")  # o pon aquí tu URL completa si la tienes

EMPRESAS = [
    'Seleccione una empresa',
    'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM',
    'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial', 'Grupo One', 'Zelva',
    'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
    'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
    'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
]

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        tipo_problema = request.form["tipo_problema"]
        descripcion = request.form["descripcion"]
        fecha_reporte = datetime.now().isoformat()

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pendiente')
                """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte))
                conn.commit()
        return render_template("gracias.html")

    return render_template("formulario.html", empresas=EMPRESAS)

@app.route("/admin")
def admin():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
            incidentes = cur.fetchall()
    return render_template("admin.html", incidentes=incidentes)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
