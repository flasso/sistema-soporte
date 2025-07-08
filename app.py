from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

DB_URL = "postgresql://sistema_soporte_db_user:GQV2H65J4INWg1fYJCFmwcKwovOPQLRn@dpg-d1lhq7p5pdvs73c0acn0-a/sistema_soporte_db"

empresas = [
    '', 'Acomedios', 'Aldas', 'Asoredes', 'Big Media', 'Cafam', 'Century', 'CNM',
    'Contructora de Marcas', 'DORTIZ', 'Elite', 'Factorial', 'Grupo One', 'Zelva',
    'Integracion', 'Inversiones CNM', 'JH Hoyos', 'Jaime Uribe', 'Maproges',
    'Media Agency', 'Media Plus', 'Multimedios', 'New Sapiens', 'OMV',
    'Quintero y Quintero', 'Servimedios', 'Teleantioquia', 'TBWA'
]

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)

def ensure_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
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
                    estado TEXT NOT NULL DEFAULT 'pendiente',
                    respuesta TEXT,
                    fecha_respuesta TIMESTAMPTZ,
                    archivo_respuesta TEXT
                );
            """)
            conn.commit()

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

        ensure_table()  # crea la tabla si no existe

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO incidentes (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (nombre, correo, telefono, empresa, tipo_problema, descripcion, fecha_reporte, estado))
                conn.commit()

        return redirect('/gracias')
    
    return render_template('formulario.html', empresas=empresas)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/admin')
def admin():
    ensure_table()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incidentes ORDER BY fecha_reporte DESC;")
            incidentes = cur.fetchall()
    return render_template('admin.html', incidentes=incidentes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
