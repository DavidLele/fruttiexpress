-- seed.sql
INSERT OR IGNORE INTO users (id, nombre, apellidos, email, telefono, password_hash, direccion, barrio, is_admin)
VALUES (1, 'Admin', 'Frutti', 'admin@frutti.com', '+57-3000000000', 'pbkdf2:sha256:150000$admin$adminhashplaceholder', 'Cra 3 #20', 'Centro', 1);

INSERT INTO products (nombre, categoria, precio, stock, unidad, tamanos, opciones, descripcion, imagen) VALUES
('Papa', 'Tuberculos', 2.50, 100, 'kg', 'pequeña,mediana,grande', '', 'Papa fresca. Calorías por 100g: 77. Buena fuente de carbohidratos.', 'papa.jpg'),
('Banano', 'Frutas', 1.20, 200, 'kg', '', 'maduro,pinton', 'Banano importado. Fuente de potasio.', 'banano.jpg'),
('Zanahoria', 'Verduras', 3.00, 80, 'kg', 'pequeña,mediana,grande', '', 'Zanahoria rica en betacaroteno. Calorías por 100g: 41.', 'zanahoria.jpg'),
('Tomate', 'Verduras', 3.50, 60, 'kg', '', '', 'Tomate jugoso para ensaladas.', 'tomate.jpg');
