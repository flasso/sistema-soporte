from flask import Flask, render_template, request, redirect, url_for
from psycopg2.extras import RealDictCursor
import psycopg2
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# URL de conexión que te dio Render
DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

# lista de empresas
EMPRESAS = [
    "Seleccione...", "Acomedios", "Aldas", "Asoredes", "Big Media", "Cafam", "Century", 
    "CNM", "Contructora de Marcas", "DORTIZ", "Elite", "Factorial", "Grupo One", "Zelva",
    "Integracion", "Inversiones CNM", "JH Hoyos", "Jaime Uribe", "Maproges", "Media Agency",
    "Media Plus", "Multimedios", "New Sapiens", "OMV", "Quintero y Quintero", "Servimedios",
    "Teleantioquia", "TBWA"
]

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidentes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT NOT NULL,
            empresa TEXT NOT NULL,
            tipo_problema TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            archivo TEXT,
            fecha_reporte TIMESTAMPTZ NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tabla 'incidentes' lista en la base de datos.")

@app.route('/', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        empresa = request.form['empresa']
        tipo_problema = request.form['tipo_problema']
        descripcion = request.form['descripcion']

        bogota_tz = pytz.timezone('America/Bogota')
        fecha_reporte = datetime.now(bogota_tz)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidentes 
            (nombre, correo, telefono, empresa, tipo_problema, descripcion, archivo, fecha_reporte, estado)
            VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, 'pendiente')
        """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('gracias'))
    return render_template('formulario.html', empresas=EMPRESAS)

@app.route('/gracias')
def gracias():
    return "<h2>Gracias por reportar el incidente. Lo atenderemos pronto.</h2>"

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
