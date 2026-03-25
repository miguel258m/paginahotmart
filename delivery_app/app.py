from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import json
import hashlib
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'delivery_secret_2024_muy_seguro')
DATABASE = os.path.join(os.path.dirname(__file__), 'delivery.db')

# ─────────────────────────────────────────────────────────────────
#  BASE DE DATOS
# ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT    NOT NULL,
        email    TEXT    UNIQUE NOT NULL,
        password TEXT    NOT NULL,
        phone    TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        email        TEXT UNIQUE NOT NULL,
        password     TEXT NOT NULL,
        phone        TEXT,
        is_available INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        description  TEXT,
        price        REAL    NOT NULL,
        category     TEXT    NOT NULL,
        emoji        TEXT    DEFAULT '🍽️',
        options      TEXT,
        is_available INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS promotions (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id          INTEGER,
        title            TEXT NOT NULL,
        description      TEXT,
        discount_percent INTEGER,
        promo_price      REAL,
        badge            TEXT,
        is_active        INTEGER DEFAULT 1,
        FOREIGN KEY (item_id) REFERENCES menu_items(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER,
        guest_name     TEXT,
        guest_phone    TEXT,
        items          TEXT    NOT NULL,
        subtotal       REAL    NOT NULL,
        delivery_fee   REAL    DEFAULT 5.00,
        total          REAL    NOT NULL,
        payment_method TEXT    NOT NULL,
        status         TEXT    DEFAULT 'pending',
        address        TEXT    NOT NULL,
        lat            REAL,
        lng            REAL,
        notes          TEXT,
        driver_id      INTEGER,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id)   REFERENCES users(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')

    count = c.execute('SELECT COUNT(*) FROM menu_items').fetchone()[0]
    if count == 0:
        _seed(c)

    conn.commit()
    conn.close()


def _seed(c):
    """Datos de ejemplo iniciales."""
    items = [
        # ── Platos ──
        ('Pollo a la Brasa',
         'Pollo entero dorado al horno con papas fritas y ensalada fresca',
         35.00, 'plato', '🍗',
         json.dumps([
             {'name': 'Tamaño', 'type': 'radio', 'required': True,
              'options': ['¼ Pollo', '½ Pollo', 'Pollo entero']},
             {'name': 'Acompañamiento', 'type': 'checkbox', 'required': False,
              'options': ['Papas fritas', 'Yuca frita', 'Ensalada', 'Arroz blanco']},
             {'name': 'Salsas', 'type': 'checkbox', 'required': False,
              'options': ['Ají verde', 'Mayonesa', 'Ketchup', 'Chimichurri']},
         ])),
        ('Lomo Saltado',
         'Tiras de lomo fino salteadas con verduras y papas fritas al wok',
         28.00, 'plato', '🥩',
         json.dumps([
             {'name': 'Punto de cocción', 'type': 'radio', 'required': True,
              'options': ['Término medio', 'Tres cuartos', 'Bien cocido']},
             {'name': 'Extras', 'type': 'checkbox', 'required': False,
              'options': ['Doble papas', 'Huevo frito', 'Sin cebolla', 'Extra arroz']},
         ])),
        ('Ceviche Clásico',
         'Pescado fresco marinado en limón con cebolla, ají, choclo y camote',
         25.00, 'plato', '🐟',
         json.dumps([
             {'name': 'Nivel de picante', 'type': 'radio', 'required': True,
              'options': ['Sin picante', 'Suave', 'Picante', 'Muy picante']},
             {'name': 'Extras', 'type': 'checkbox', 'required': False,
              'options': ['Choclo extra', 'Camote extra', 'Cancha extra', 'Chicharrón']},
         ])),
        ('Pizza Margarita',
         'Salsa de tomate artesanal, mozzarella fresca y albahaca',
         22.00, 'plato', '🍕',
         json.dumps([
             {'name': 'Tamaño', 'type': 'radio', 'required': True,
              'options': ['Personal 25 cm', 'Mediana 33 cm', 'Familiar 40 cm']},
             {'name': 'Toppings extra', 'type': 'checkbox', 'required': False,
              'options': ['Extra queso', 'Champiñones', 'Aceitunas', 'Pimiento rojo']},
             {'name': 'Tipo de masa', 'type': 'radio', 'required': True,
              'options': ['Tradicional', 'Delgada', 'Integral']},
         ])),
        ('Hamburguesa Clásica',
         'Carne de res 180 g, lechuga, tomate, cebolla y queso cheddar',
         18.00, 'plato', '🍔',
         json.dumps([
             {'name': 'Término de carne', 'type': 'radio', 'required': True,
              'options': ['Bien cocida', 'Tres cuartos', 'Término medio']},
             {'name': 'Agregar extras', 'type': 'checkbox', 'required': False,
              'options': ['Doble carne +S/5', 'Tocino +S/3', 'Huevo frito +S/2',
                          'Queso extra +S/2', 'Palta/Aguacate +S/4']},
             {'name': 'Quitar ingredientes', 'type': 'checkbox', 'required': False,
              'options': ['Sin cebolla', 'Sin tomate', 'Sin lechuga', 'Sin queso']},
         ])),
        ('Pasta Alfredo',
         'Fettuccine en salsa cremosa de queso parmesano recién rallado',
         20.00, 'plato', '🍝',
         json.dumps([
             {'name': 'Proteína', 'type': 'radio', 'required': True,
              'options': ['Solo pasta', 'Con pollo', 'Con camarones', 'Con champiñones']},
             {'name': 'Extras', 'type': 'checkbox', 'required': False,
              'options': ['Doble salsa', 'Extra parmesano']},
         ])),

        # ── Bebidas ──
        ('Coca Cola',
         'Bebida refrescante clásica bien fría',
         4.00, 'bebida', '🥤',
         json.dumps([
             {'name': 'Tamaño', 'type': 'radio', 'required': True,
              'options': ['Personal 400 ml', 'Grande 600 ml', 'Litro 1 L']},
             {'name': 'Temperatura', 'type': 'radio', 'required': False,
              'options': ['Con hielo', 'Sin hielo', 'Extra fría']},
         ])),
        ('Limonada Natural',
         'Limonada fresca exprimida al momento con menta y hielo',
         6.00, 'bebida', '🍋',
         json.dumps([
             {'name': 'Variedad', 'type': 'radio', 'required': True,
              'options': ['Clásica', 'Con fresa', 'Con maracuyá', 'Con menta']},
             {'name': 'Dulzura', 'type': 'radio', 'required': False,
              'options': ['Sin azúcar', 'Poco dulce', 'Normal', 'Extra dulce']},
         ])),
        ('Agua Mineral',
         'Agua natural purificada de 600 ml bien fría',
         2.50, 'bebida', '💧',
         json.dumps([
             {'name': 'Tipo', 'type': 'radio', 'required': True,
              'options': ['Sin gas', 'Con gas']},
         ])),
        ('Jugo Natural del Día',
         'Jugo de fruta fresca preparado al momento sin conservantes',
         7.00, 'bebida', '🍊',
         json.dumps([
             {'name': 'Sabor', 'type': 'radio', 'required': True,
              'options': ['Naranja', 'Mango', 'Piña', 'Maracuyá', 'Fresa', 'Mix tropical']},
             {'name': 'Tamaño', 'type': 'radio', 'required': True,
              'options': ['Regular 300 ml', 'Grande 500 ml']},
         ])),
    ]

    item_ids = []
    for it in items:
        c.execute(
            'INSERT INTO menu_items (name, description, price, category, emoji, options) '
            'VALUES (?, ?, ?, ?, ?, ?)', it)
        item_ids.append(c.lastrowid)

    promos = [
        (item_ids[0], '🔥 Combo Familiar — Pollo a la Brasa',
         'Pollo entero + 2 bebidas por precio especial', 20, None, '20% OFF'),
        (item_ids[3], '🍕 2×1 en Pizzas Medianas',
         'Pide 2 pizzas medianas y paga solo 1', 50, None, '2×1'),
        (item_ids[4], '🍔 Hamburguesa + Bebida Combo',
         'Hamburguesa clásica + cualquier bebida por S/ 20', None, 20.00, 'COMBO'),
    ]
    for p in promos:
        c.execute(
            'INSERT INTO promotions '
            '(item_id, title, description, discount_percent, promo_price, badge, is_active) '
            'VALUES (?, ?, ?, ?, ?, ?, 1)', p)

    driver_pw = hashlib.sha256('driver123'.encode()).hexdigest()
    c.execute(
        'INSERT OR IGNORE INTO drivers (name, email, password, phone) VALUES (?, ?, ?, ?)',
        ('Carlos García', 'driver@delivery.com', driver_pw, '999-888-777'))


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Inicia sesión para continuar.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'driver_id' not in session:
            return redirect(url_for('driver_login'))
        return f(*args, **kwargs)
    return decorated


def parse_item(row):
    d = dict(row)
    d['options'] = json.loads(row['options']) if row['options'] else []
    return d


# ─────────────────────────────────────────────────────────────────
#  RUTAS  –  CLIENTES
# ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('menu'))
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    name     = request.form['name'].strip()
    email    = request.form['email'].strip().lower()
    password = request.form['password']
    phone    = request.form.get('phone', '').strip()

    if not name or not email or not password:
        flash('Por favor completa todos los campos requeridos.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)',
            (name, email, hash_pw(password), phone))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        flash(f'¡Bienvenido/a, {name}! Tu cuenta fue creada.', 'success')
        return redirect(url_for('menu'))
    except sqlite3.IntegrityError:
        flash('Ese correo ya está registrado. Inicia sesión.', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    email    = request.form['email'].strip().lower()
    password = request.form['password']

    conn   = get_db()
    user   = conn.execute(
        'SELECT * FROM users WHERE email = ? AND password = ?',
        (email, hash_pw(password))).fetchone()
    conn.close()

    if user:
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        return redirect(url_for('menu'))
    else:
        flash('Correo o contraseña incorrectos.', 'error')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ── Menú ──────────────────────────────────────────────────────────

@app.route('/menu')
def menu():
    conn   = get_db()
    items  = conn.execute(
        'SELECT * FROM menu_items WHERE is_available = 1 ORDER BY category').fetchall()
    promos = conn.execute('''
        SELECT p.*, m.name AS item_name, m.price AS original_price,
               m.emoji, m.description AS item_desc
        FROM   promotions p
        JOIN   menu_items m ON p.item_id = m.id
        WHERE  p.is_active = 1
    ''').fetchall()
    conn.close()

    platos  = [parse_item(i) for i in items if i['category'] == 'plato']
    bebidas = [parse_item(i) for i in items if i['category'] == 'bebida']

    return render_template('menu.html',
                           platos=platos,
                           bebidas=bebidas,
                           promos=[dict(p) for p in promos])


@app.route('/api/item/<int:item_id>')
def get_item(item_id):
    conn = get_db()
    item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    if item:
        return jsonify(parse_item(item))
    return jsonify({'error': 'Not found'}), 404


# ── Carrito (sesión) ──────────────────────────────────────────────

@app.route('/api/cart', methods=['GET'])
def get_cart():
    return jsonify(session.get('cart', []))


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    cart = session.get('cart', [])
    cart.append(data)
    session['cart']    = cart
    session.modified   = True
    return jsonify({'count': len(cart), 'cart': cart})


@app.route('/api/cart/remove/<int:index>', methods=['DELETE'])
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart']  = cart
        session.modified = True
    return jsonify({'count': len(cart), 'cart': cart})


@app.route('/api/cart/clear', methods=['DELETE'])
def clear_cart():
    session['cart']  = []
    session.modified = True
    return jsonify({'count': 0})


# ── Checkout ──────────────────────────────────────────────────────

@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('menu'))
    return render_template('checkout.html', cart=cart)


@app.route('/order/place', methods=['POST'])
def place_order():
    cart = session.get('cart', [])
    if not cart:
        return redirect(url_for('menu'))

    f              = request.form
    address        = f.get('address', '').strip()
    lat            = f.get('lat', '')
    lng            = f.get('lng', '')
    payment        = f.get('payment_method', 'efectivo')
    notes          = f.get('notes', '').strip()
    guest_name     = f.get('guest_name', '').strip()
    guest_phone    = f.get('guest_phone', '').strip()

    if not address:
        flash('Por favor ingresa tu dirección de entrega.', 'error')
        return redirect(url_for('checkout'))

    subtotal     = sum(float(i.get('price', 0)) * int(i.get('qty', 1)) for i in cart)
    delivery_fee = 5.00
    total        = subtotal + delivery_fee

    conn    = get_db()
    user_id = session.get('user_id')

    if user_id:
        user        = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        guest_name  = user['name']
        guest_phone = user['phone'] or ''

    cursor = conn.execute('''
        INSERT INTO orders
            (user_id, guest_name, guest_phone, items, subtotal, delivery_fee,
             total, payment_method, address, lat, lng, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, guest_name, guest_phone, json.dumps(cart),
          subtotal, delivery_fee, total, payment, address,
          float(lat) if lat else None,
          float(lng) if lng else None,
          notes))

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session['cart']  = []
    session.modified = True

    return redirect(url_for('order_success', order_id=order_id))


@app.route('/order/success/<int:order_id>')
def order_success(order_id):
    conn  = get_db()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if not order:
        return redirect(url_for('menu'))
    od          = dict(order)
    od['items'] = json.loads(order['items'])
    return render_template('order_success.html', order=od)


# ─────────────────────────────────────────────────────────────────
#  RUTAS  –  MOTORIZADO
# ─────────────────────────────────────────────────────────────────

@app.route('/driver')
def driver_login():
    if 'driver_id' in session:
        return redirect(url_for('driver_dashboard'))
    return render_template('driver_login.html')


@app.route('/driver/login', methods=['POST'])
def driver_login_post():
    email    = request.form['email'].strip().lower()
    password = request.form['password']

    conn   = get_db()
    driver = conn.execute(
        'SELECT * FROM drivers WHERE email = ? AND password = ?',
        (email, hash_pw(password))).fetchone()
    conn.close()

    if driver:
        session['driver_id']   = driver['id']
        session['driver_name'] = driver['name']
        return redirect(url_for('driver_dashboard'))
    else:
        flash('Credenciales incorrectas.', 'error')
        return redirect(url_for('driver_login'))


@app.route('/driver/logout')
def driver_logout():
    session.pop('driver_id',   None)
    session.pop('driver_name', None)
    return redirect(url_for('driver_login'))


@app.route('/driver/dashboard')
@driver_required
def driver_dashboard():
    conn   = get_db()
    orders = conn.execute('''
        SELECT * FROM orders
        WHERE  status IN ('pending', 'preparing', 'on_way')
        ORDER  BY created_at DESC
    ''').fetchall()
    conn.close()

    result = []
    for o in orders:
        d              = dict(o)
        d['items']     = json.loads(o['items'])
        d['items_sum'] = sum(it.get('qty', 1) for it in d['items'])
        result.append(d)

    return render_template('driver_dashboard.html', orders=result)


@app.route('/driver/order/<int:order_id>/status', methods=['POST'])
@driver_required
def update_order_status(order_id):
    new_status = request.json.get('status')
    valid      = ['pending', 'preparing', 'on_way', 'delivered', 'cancelled']
    if new_status not in valid:
        return jsonify({'error': 'Estado inválido'}), 400

    conn = get_db()
    conn.execute(
        'UPDATE orders SET status = ?, driver_id = ? WHERE id = ?',
        (new_status, session['driver_id'], order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'status': new_status})


@app.route('/driver/api/orders')
@driver_required
def driver_orders_api():
    conn   = get_db()
    orders = conn.execute('''
        SELECT * FROM orders
        WHERE  status IN ('pending', 'preparing', 'on_way')
        ORDER  BY created_at DESC
    ''').fetchall()
    conn.close()

    result = []
    for o in orders:
        d          = dict(o)
        d['items'] = json.loads(o['items'])
        result.append(d)
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print('\n' + '=' * 55)
    print('  🚀  Servidor de Delivery iniciado!')
    print('=' * 55)
    print('  📱  Clientes  →  http://localhost:5000')
    print('  🏍️   Motorizado →  http://localhost:5000/driver')
    print('       Email    :  driver@delivery.com')
    print('       Password :  driver123')
    print('=' * 55 + '\n')
    app.run(debug=True, port=5000)
