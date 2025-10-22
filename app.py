# app.py
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path

DB_PATH = 'frutti.db'

app = Flask(__name__)
app.secret_key = 'clave_segura_frutti_123!'

# ---------------- DB helpers ----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

# Init DB if missing
def init_db():
    if not Path(DB_PATH).exists():
        with app.app_context():
            db = get_db()
            try:
                with open('schema.sql', 'r', encoding='utf-8') as f:
                    db.executescript(f.read())
            except FileNotFoundError:
                pass
            try:
                with open('seed.sql', 'r', encoding='utf-8') as f:
                    db.executescript(f.read())
            except FileNotFoundError:
                pass
            db.commit()

@app.before_first_request
def startup():
    init_db()

# ---------------- helpers ----------------
def current_user():
    if 'user_id' not in session:
        return None
    return query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)

def is_logged_in():
    return 'user_id' in session

# ---------------- rutas ----------------
@app.route('/')
def index():
    frutas = query_db("SELECT * FROM products WHERE categoria='Frutas' LIMIT 10")
    verduras = query_db("SELECT * FROM products WHERE categoria='Verduras' LIMIT 10")
    tuberculos = query_db("SELECT * FROM products WHERE categoria='Tuberculos' LIMIT 10")
    otro = query_db("SELECT * FROM products WHERE categoria='Otro' LIMIT 10")
    return render_template('index.html', frutas=frutas, verduras=verduras, tuberculos=tuberculos, otro=otro, user=current_user())

@app.route('/buscar')
def buscar():
    q = request.args.get('q','').strip()
    productos = []
    if q:
        like = f"%{q}%"
        productos = query_db("SELECT * FROM products WHERE nombre LIKE ? OR descripcion LIKE ?", [like, like])
    return render_template('category.html', categoria=f"Resultados: {q}", productos=productos, user=current_user())

@app.route('/categoria/<nombre>')
def categoria(nombre):
    productos = query_db("SELECT * FROM products WHERE categoria = ?", [nombre])
    return render_template('category.html', categoria=nombre, productos=productos, user=current_user())

@app.route('/producto/<int:pid>')
def producto(pid):
    p = query_db("SELECT * FROM products WHERE id = ?", [pid], one=True)
    if not p:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('index'))
    return render_template('product.html', producto=p, user=current_user())

# ---------------- auth ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre','').strip()
        apellidos = request.form.get('apellidos','').strip()
        email = request.form.get('email','').strip().lower()
        telefono = request.form.get('telefono','').strip()
        password = request.form.get('password','')
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        try:
            execute_db("INSERT INTO users (nombre, apellidos, email, telefono, password_hash) VALUES (?,?,?,?,?)",
                       [nombre, apellidos, email, telefono, hashed])
            flash('Registro exitoso', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Error: ese correo ya está en uso.', 'error')
            return redirect(url_for('register'))
    return render_template('register.html', user=current_user())

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        u = query_db('SELECT * FROM users WHERE email = ?', [email], one=True)
        if u and check_password_hash(u['password_hash'], password):
            session['user_id'] = u['id']
            session['is_admin'] = bool(u['is_admin'])
            flash('Sesión iniciada correctamente', 'success')
            return redirect(url_for('index'))
        flash('Credenciales incorrectas', 'error')
        return redirect(url_for('login'))
    return render_template('login.html', user=current_user())

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('index'))

# ---------------- perfil ----------------
@app.route('/perfil', methods=['GET','POST'])
def perfil():
    if not is_logged_in():
        return redirect(url_for('login'))
    u = current_user()
    if request.method == 'POST':
        direccion = request.form.get('direccion','').strip()
        telefono = request.form.get('telefono','').strip()
        execute_db("UPDATE users SET direccion=?, telefono=? WHERE id = ?", [direccion, telefono, u['id']])
        flash('Perfil actualizado', 'success')
        return redirect(url_for('perfil'))
    return render_template('profile.html', user=u)

# ---------------- carrito ----------------
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for key, v in cart.items():
        pid = int(key)
        p = query_db("SELECT * FROM products WHERE id = ?", [pid], one=True)
        if not p: continue
        subtotal = v['cantidad'] * p['precio']
        total += subtotal
        items.append({'product':p, 'cantidad': v['cantidad'], 'unidad': v.get('unidad','kg'), 'tamanio': v.get('tamanio',''), 'opcion': v.get('opcion',''), 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total, user=current_user())

@app.route('/cart/add', methods=['POST'])
def cart_add():
    data = request.form
    pid = data.get('product_id')
    cantidad = float(data.get('cantidad', 1))
    unidad = data.get('unidad','kg')
    tamanio = data.get('tamanio','')
    opcion = data.get('opcion','')
    if not pid:
        return redirect(url_for('index'))
    cart = session.get('cart', {})
    if pid in cart:
        cart[pid]['cantidad'] += cantidad
    else:
        cart[pid] = {'cantidad': cantidad, 'unidad': unidad, 'tamanio': tamanio, 'opcion': opcion}
    session['cart'] = cart
    flash('Producto añadido al carrito', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart/remove/<int:pid>')
def cart_remove(pid):
    cart = session.get('cart', {})
    if str(pid) in cart:
        del cart[str(pid)]
        session['cart'] = cart
        flash('Producto eliminado', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if not is_logged_in():
        flash('Debe iniciar sesión para comprar', 'error')
        return redirect(url_for('login'))
    user = current_user()
    cart = session.get('cart', {})
    if not cart:
        flash('Carrito vacío', 'error')
        return redirect(url_for('cart'))
    total = 0.0
    for key, v in cart.items():
        p = query_db('SELECT * FROM products WHERE id = ?', [key], one=True)
        if not p: continue
        total += v['cantidad'] * p['precio']
    notas = request.form.get('notas','')
    order_id = execute_db("INSERT INTO orders (user_id, total, notas) VALUES (?,?,?)", [user['id'], total, notas])
    for key, v in cart.items():
        p = query_db('SELECT * FROM products WHERE id = ?', [key], one=True)
        execute_db("""INSERT INTO order_items (order_id, product_id, cantidad, unidad, tamanio, opcion, precio_unit)
                      VALUES (?,?,?,?,?,?,?)""", [order_id, key, v['cantidad'], v.get('unidad','kg'), v.get('tamanio',''), v.get('opcion',''), p['precio']])
    session['cart'] = {}
    flash('Pedido realizado con éxito', 'success')
    return redirect(url_for('index'))

# ---------------- admin ----------------
def require_admin():
    u = current_user()
    if not u or u['is_admin'] != 1:
        flash('Acceso denegado', 'error')
        return False
    return True

@app.route('/admin')
def admin_dashboard():
    if not require_admin():
        return redirect(url_for('login'))
    pedidos = query_db("""
        SELECT 
            o.id AS id,
            o.total,
            o.created_at,
            o.notas,
            u.nombre AS cliente,
            u.email,
            u.telefono,
            u.direccion
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """)
    return render_template('admin_dashboard.html', pedidos=pedidos, user=current_user())

@app.route('/admin/products', methods=['GET','POST'])
def admin_products():
    if not require_admin():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        categoria = request.form.get('categoria')
        precio = float(request.form.get('precio') or 0)
        stock = float(request.form.get('stock') or 0)
        # 👇 Permitir múltiples unidades separadas por coma
        unidad = request.form.get('unidad','kg').strip()
        tamanos = request.form.get('tamanos','')
        opciones = request.form.get('opciones','')
        descripcion = request.form.get('descripcion','')
        imagen = request.form.get('imagen','')
        execute_db("""INSERT INTO products (nombre, categoria, precio, stock, unidad, tamanos, opciones, descripcion, imagen)
                      VALUES (?,?,?,?,?,?,?,?,?)""", [nombre, categoria, precio, stock, unidad, tamanos, opciones, descripcion, imagen])
        flash('Producto creado correctamente', 'success')
        return redirect(url_for('admin_products'))
    productos = query_db('SELECT * FROM products')
    return render_template('admin_products.html', productos=productos, user=current_user())

@app.route('/admin/orders/<int:oid>')
def admin_order_detail(oid):
    if not require_admin():
        return redirect(url_for('login'))
    order = query_db("""
        SELECT 
            o.id AS id,
            o.total,
            o.created_at,
            o.notas,
            u.nombre AS cliente,
            u.email,
            u.telefono,
            u.direccion
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    """, [oid], one=True)
    items = query_db("""
        SELECT oi.*, p.nombre 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        WHERE oi.order_id = ?
    """, [oid])
    return render_template('admin_orders.html', order=order, items=items, user=current_user())

# ---------------- run ----------------
if __name__ == '__main__':
    app.run(debug=True)
