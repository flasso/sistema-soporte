from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

DB_URL = os.getenv("DB_URL", "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db")

EMPRESAS = [
    'Seleccione una empresa', 'Acomedios', 'Aldas', 'Adela', 'Asoredes', 'Big Media', 'Cafam',
    'Century', 'CNM', 'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial',
    'Grupo One', 'Zelva', 'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe',
    'Maproges', 'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
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
        tipo = request.form['tipo_problema']
        descripcion = request.form['descripcion']
        fecha = datetime.now(timezone.utc) - timedelta(hours=5)  # Colombia UTC-5
        estado = 'pendiente'

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (nombre, correo, telefono, empresa, tipo, descripcion, fecha, estado))
                conn.commit()
        return redirect(url_for('gracias'))
    return render_template('formulario.html', empresas=EMPRESAS)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin')
def admin():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC")
            incidentes = cur.fetchall()
    return render_template('admin.html', incidentes=incidentes)

@app.route('/index')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
