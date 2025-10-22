# create_admin.py
# Script sencillo para crear/actualizar un usuario administrador en frutti.db
import sqlite3
import getpass
from werkzeug.security import generate_password_hash
from pathlib import Path

DB_PATH = 'frutti.db'  # coincide con app.py

def ensure_db_exists():
    # Si no existe la BD, avisamos (app.py normalmente la crea al iniciar)
    p = Path(DB_PATH)
    if not p.exists():
        print(f"Atención: '{DB_PATH}' no existe en la carpeta actual.")
        print("Inicia la app (python app.py) una vez para que se cree la BD, o coloca frutti.db en esta carpeta.")
        return False
    return True

def create_or_update_admin(nombre, apellidos, email, telefono, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # normalizar email
    email = email.strip().lower()
    password_hash = generate_password_hash(password)

    # Comprobar si el usuario ya existe
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        cur.execute("""
            UPDATE users
            SET nombre = ?, apellidos = ?, telefono = ?, password_hash = ?, is_admin = 1
            WHERE id = ?
        """, (nombre, apellidos, telefono, password_hash, user_id))
        print(f"Usuario existente actualizado y convertido en admin (id={user_id}).")
    else:
        cur.execute("""
            INSERT INTO users (nombre, apellidos, email, telefono, password_hash, is_admin)
            VALUES (?,?,?,?,?,1)
        """, (nombre, apellidos, email, telefono, password_hash))
        user_id = cur.lastrowid
        print(f"Usuario administrador creado (id={user_id}).")
    conn.commit()
    conn.close()
    print("Listo. Ahora puedes iniciar sesión con ese correo y contraseña.")

if __name__ == '__main__':
    if not ensure_db_exists():
        # pedimos si quieren que intentemos crear la BD ejecutando schema.sql (opcional)
        resp = input("¿Deseas ejecutar schema.sql ahora para crear tablas básicas? (s/n) ").strip().lower()
        if resp == 's':
            try:
                with open('schema.sql', 'r', encoding='utf-8') as f:
                    sql = f.read()
                conn = sqlite3.connect(DB_PATH)
                conn.executescript(sql)
                conn.commit()
                conn.close()
                print("schema.sql ejecutado. BD inicializada.")
            except Exception as e:
                print("No se pudo ejecutar schema.sql:", e)
        else:
            print("Cancela y coloca frutti.db en la carpeta o inicia app.py primero.")
            exit(1)

    print("=== Crear / Convertir usuario en ADMIN ===")
    nombre = input("Nombre (ej: Admin): ").strip() or "Admin"
    apellidos = input("Apellidos (opcional): ").strip()
    email = input("Email (ej: admin@fruttiexpress.com): ").strip() or "admin@fruttiexpress.com"
    telefono = input("Teléfono (opcional): ").strip()
    # usar getpass para no mostrar la contraseña
    while True:
        password = getpass.getpass("Contraseña (mínimo 6 chars): ")
        if len(password) < 6:
            print("Contraseña muy corta, inténtalo de nuevo.")
            continue
        password2 = getpass.getpass("Confirma contraseña: ")
        if password != password2:
            print("No coinciden, intenta otra vez.")
            continue
        break

    create_or_update_admin(nombre, apellidos, email, telefono, password)
