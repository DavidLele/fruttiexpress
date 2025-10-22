-- schema.sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT,
    email TEXT UNIQUE NOT NULL,
    telefono TEXT,
    password_hash TEXT NOT NULL,
    direccion TEXT,
    barrio TEXT,
    is_admin INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL, -- 'Frutas','Verduras','Tuberculos','Otro'
    precio REAL NOT NULL,
    stock REAL DEFAULT 0, -- en kilos o unidades
    unidad TEXT DEFAULT 'kg', -- 'kg' o 'unit'
    tamanos TEXT, -- ejemplo: "pequeña,mediana,grande" (csv)
    opciones TEXT, -- ejemplo: "maduro,pinton" para banano
    descripcion TEXT,
    imagen TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total REAL,
    notas TEXT,
    estado TEXT DEFAULT 'Pendiente',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    cantidad REAL,
    unidad TEXT,
    tamanio TEXT,
    opcion TEXT,
    precio_unit REAL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);
