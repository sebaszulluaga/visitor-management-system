import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave más segura

# Conectar a la base de datos y crear las tablas si no existen
def init_db():
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    
    # Crear tabla de registro de entradas y salidas
    cursor.execute('''CREATE TABLE IF NOT EXISTS registro_entrada_salida (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        residente_id TEXT,
        nombre TEXT,
        cuarto TEXT,
        fecha TEXT,
        hora TEXT,
        tipo_movimiento TEXT
    )''')

    # Crear tabla de residentes
    cursor.execute('''CREATE TABLE IF NOT EXISTS residentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cuarto TEXT NOT NULL,
        fecha_ingreso TEXT NOT NULL,
        fecha_salida TEXT
    )''')

    conn.commit()
    conn.close()

# Funciones de base de datos
def guardar_en_base_de_datos(residente_id, nombre, cuarto, tipo_movimiento):
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")
    cursor.execute('''INSERT INTO registro_entrada_salida (residente_id, nombre, cuarto, fecha, hora, tipo_movimiento)
                      VALUES (?, ?, ?, ?, ?, ?)''', (residente_id, nombre, cuarto, fecha, hora, tipo_movimiento))
    conn.commit()
    conn.close()

def obtener_registros(mes=None):
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM registro_entrada_salida'
    
    if mes:
        query += ' WHERE strftime("%m", fecha) = ?'
        cursor.execute(query, (mes,))
    else:
        cursor.execute(query)
    
    registros = cursor.fetchall()
    conn.close()
    
    # Agrupar registros por habitación
    registros_por_habitacion = {}
    for registro in registros:
        cuarto = registro[3]  # Suponiendo que 'cuarto' es el cuarto en la posición 3
        if cuarto not in registros_por_habitacion:
            registros_por_habitacion[cuarto] = []
        registros_por_habitacion[cuarto].append(registro)
    
    return registros_por_habitacion

def obtener_info_residente(residente_id):
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, cuarto FROM residentes WHERE id = ?', (residente_id,))
    residente = cursor.fetchone()
    conn.close()
    return residente

def agregar_residente(nombre, cuarto):
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    fecha_ingreso = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''INSERT INTO residentes (nombre, cuarto, fecha_ingreso) VALUES (?, ?, ?)''', (nombre, cuarto, fecha_ingreso))
    conn.commit()
    conn.close()

def actualizar_residente(id_residente, nuevo_cuarto):
    conn = sqlite3.connect('residencia.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE residentes SET cuarto = ? WHERE id = ?', (nuevo_cuarto, id_residente))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capturar', methods=['POST'])
def capturar():
    residente_id = request.form['codigo']
    tipo_movimiento = request.form['tipo_movimiento']
    if tipo_movimiento not in ['entrada', 'salida']:
        return "Tipo de movimiento no válido.", 400

    residente_info = obtener_info_residente(residente_id)
    if residente_info:
        nombre, cuarto = residente_info
        guardar_en_base_de_datos(residente_id, nombre, cuarto, tipo_movimiento)
    else:
        return "Residente no encontrado.", 404

    return redirect(url_for('index'))

@app.route('/agregar_residente', methods=['GET', 'POST'])
def agregar_residente_view():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cuarto = request.form['cuarto']
        agregar_residente(nombre, cuarto)
        return redirect(url_for('index'))
    return render_template('agregar_residente.html')

@app.route('/actualizar_residente', methods=['GET', 'POST'])
def actualizar_residente_view():
    if request.method == 'POST':
        id_residente = request.form['id_residente']
        nuevo_cuarto = request.form['nuevo_cuarto']
        actualizar_residente(id_residente, nuevo_cuarto)
        return redirect(url_for('index'))
    return render_template('actualizar_residente.html')

@app.route('/ver_registros', methods=['GET', 'POST'])
def ver_registros():
    if 'admin_logged_in' not in session:
        return redirect(url_for('index'))  # Redirige si no está autenticado

    mes = request.form.get('mes')  # Obtiene el mes del formulario
    registros = obtener_registros(mes)
    return render_template('ver_registros.html', registros=registros)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Aquí puedes implementar tu lógica de autenticación
        if username == 'admin' and password == 'admin':  # Cambia esto por tu lógica de autenticación
            session['admin_logged_in'] = True
            return redirect(url_for('ver_registros'))
        else:
            return "Credenciales incorrectas", 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Iniciar la base de datos
init_db()

# Iniciar el servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
