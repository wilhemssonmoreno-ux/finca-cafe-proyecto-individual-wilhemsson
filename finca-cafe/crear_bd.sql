-- crear_bd.sql · Finca de café · Programación III (IS-151)
-- Crea la base desde cero e inserta datos de prueba.
-- Uso:  sqlite3 finca.db < crear_bd.sql   (o dejar que la API lo haga sola al iniciar)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tokens;
DROP TABLE IF EXISTS produccion_cafe;
DROP TABLE IF EXISTS cosechas;
DROP TABLE IF EXISTS ventas_cafe;
DROP TABLE IF EXISTS tarifas;
DROP TABLE IF EXISTS trabajadores;
DROP TABLE IF EXISTS lotes;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE lotes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL UNIQUE CHECK (length(trim(nombre)) >= 2),
    variedad  TEXT NOT NULL CHECK (length(trim(variedad)) >= 2),
    hectareas REAL NOT NULL CHECK (hectareas > 0)
);

CREATE TABLE trabajadores (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL CHECK (length(trim(nombre)) >= 3),
    identidad TEXT NOT NULL UNIQUE CHECK (length(identidad) = 15),   -- 0301-1990-12345
    telefono  TEXT NOT NULL CHECK (length(telefono) = 9)             -- 9999-9999
);

CREATE TABLE tarifas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    temporada       TEXT NOT NULL UNIQUE,
    precio_por_lata REAL NOT NULL CHECK (precio_por_lata > 0),
    fecha_inicio    TEXT NOT NULL,   -- AAAA-MM-DD
    fecha_fin       TEXT NOT NULL,
    CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE cosechas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id       INTEGER NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id) ON DELETE RESTRICT,
    fecha         TEXT NOT NULL,
    latas         INTEGER NOT NULL CHECK (latas > 0),
    UNIQUE (lote_id, trabajador_id, fecha)   -- un registro por trabajador, lote y día
);
CREATE INDEX idx_cosechas_fecha ON cosechas(fecha);

CREATE TABLE produccion_cafe (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id   INTEGER NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    fecha     TEXT NOT NULL,                         -- día en que el café quedó listo en bodega
    quintales REAL NOT NULL CHECK (quintales > 0)
);
CREATE INDEX idx_produccion_fecha ON produccion_cafe(fecha);

CREATE TABLE ventas_cafe (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha         TEXT NOT NULL,
    comprador     TEXT NOT NULL CHECK (length(trim(comprador)) >= 2),
    quintales     REAL NOT NULL CHECK (quintales > 0),
    precio_quintal REAL NOT NULL CHECK (precio_quintal > 0)
);

CREATE TABLE usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario       TEXT NOT NULL UNIQUE CHECK (length(usuario) >= 3),
    nombre        TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE tokens (
    token      TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    creado     TEXT NOT NULL,
    expira     TEXT NOT NULL
);

-- Datos de prueba

INSERT INTO lotes (nombre, variedad, hectareas) VALUES
  ('El Mirador', 'Catuaí', 3.5),
  ('La Cumbre', 'Lempira', 4.0),
  ('Los Pinos', 'IHCAFE 90', 2.5),
  ('San Isidro', 'Parainema', 5.0),
  ('El Carrizal', 'Bourbon', 1.8),
  ('La Esperanza', 'Caturra', 3.0),
  ('Monte Verde', 'Catuaí', 2.2),
  ('El Naranjo', 'Typica', 1.5),
  ('Las Nubes', 'Pacas', 2.8),
  ('Cerro Azul', 'Lempira', 4.5);

INSERT INTO trabajadores (nombre, identidad, telefono) VALUES
  ('José Armando Reyes', '0301-1988-04512', '9876-5521'),
  ('María Elena Cruz', '0301-1992-01877', '3344-2190'),
  ('Carlos Ernesto Mejía', '0301-1985-07741', '9912-4403'),
  ('Ana Lucía Flores', '0301-1996-02265', '8855-1076'),
  ('Santos Efraín Medina', '0301-1979-00934', '9701-8832'),
  ('Rosa Margarita Villanueva', '0301-1990-05619', '3290-7741'),
  ('Dilcia Noemí Paz', '0301-1994-03388', '9633-2015'),
  ('Wilmer Antonio Sosa', '0301-1987-06102', '8812-9954'),
  ('Lesly Yamileth Ortiz', '0301-1999-00471', '9455-6620'),
  ('Marvin Josué Alvarado', '0301-1993-04096', '3187-5528'),
  ('Elvia Patricia Banegas', '0301-1982-02753', '9528-3317'),
  ('Héctor Danilo Rivera', '0301-1991-01604', '8690-4471'),
  ('Nelly Soraya Ramos', '0301-1997-05230', '9344-1186'),
  ('Óscar René Castellanos', '0301-1984-03917', '3052-9063');

INSERT INTO tarifas (temporada, precio_por_lata, fecha_inicio, fecha_fin) VALUES
  ('Cosecha 2024-2025', 28.0, '2024-11-01', '2025-10-31'),
  ('Cosecha 2025-2026', 32.0, '2025-11-01', '2026-10-31'),
  ('Cosecha 2026-2027', 35.0, '2026-11-01', '2027-10-31');

INSERT INTO cosechas (lote_id, trabajador_id, fecha, latas) VALUES
  (5, 11, '2026-10-19', 18),
  (5, 12, '2026-10-19', 30),
  (9, 10, '2026-10-19', 29),
  (2, 5, '2026-10-20', 30),
  (4, 14, '2026-10-20', 34),
  (6, 11, '2026-10-20', 30),
  (7, 8, '2026-10-20', 39),
  (1, 9, '2026-10-21', 55),
  (3, 13, '2026-10-21', 24),
  (5, 14, '2026-10-21', 24),
  (9, 11, '2026-10-21', 56),
  (1, 2, '2026-10-22', 19),
  (5, 10, '2026-10-22', 27),
  (7, 6, '2026-10-22', 39),
  (2, 8, '2026-10-23', 51),
  (2, 11, '2026-10-23', 45),
  (6, 2, '2026-10-23', 25),
  (10, 10, '2026-10-23', 54),
  (2, 8, '2026-10-24', 21),
  (8, 4, '2026-10-24', 32),
  (9, 5, '2026-10-24', 30),
  (10, 11, '2026-10-24', 27),
  (1, 5, '2026-10-26', 24),
  (7, 14, '2026-10-26', 21),
  (9, 2, '2026-10-26', 51),
  (3, 7, '2026-10-27', 48),
  (5, 11, '2026-10-27', 45),
  (7, 8, '2026-10-27', 43),
  (5, 7, '2026-10-28', 44),
  (7, 14, '2026-10-28', 29),
  (8, 2, '2026-10-28', 18),
  (8, 10, '2026-10-28', 53),
  (1, 8, '2026-10-29', 39),
  (6, 5, '2026-10-29', 50),
  (7, 12, '2026-10-29', 15),
  (10, 3, '2026-10-29', 42),
  (1, 5, '2026-10-30', 54),
  (5, 13, '2026-10-30', 20),
  (9, 6, '2026-10-30', 44),
  (9, 8, '2026-10-30', 26),
  (1, 2, '2026-10-31', 14),
  (5, 4, '2026-10-31', 47),
  (6, 5, '2026-10-31', 30),
  (10, 1, '2026-10-31', 46),
  (1, 1, '2026-11-02', 28),
  (5, 3, '2026-11-02', 46),
  (5, 4, '2026-11-02', 25),
  (6, 4, '2026-11-03', 32),
  (6, 10, '2026-11-03', 16),
  (9, 11, '2026-11-03', 52),
  (4, 3, '2026-11-04', 38),
  (4, 13, '2026-11-04', 37),
  (8, 14, '2026-11-04', 38),
  (9, 9, '2026-11-04', 49),
  (3, 4, '2026-11-05', 26),
  (5, 1, '2026-11-05', 20),
  (6, 10, '2026-11-05', 19),
  (7, 8, '2026-11-05', 44),
  (5, 12, '2026-11-06', 45),
  (8, 3, '2026-11-06', 22),
  (9, 4, '2026-11-06', 38),
  (3, 5, '2026-11-07', 42),
  (6, 13, '2026-11-07', 48),
  (7, 2, '2026-11-07', 40);

INSERT INTO produccion_cafe (lote_id, fecha, quintales) VALUES
  (1, '2025-12-05', 8.0),
  (2, '2025-12-05', 9.5),
  (3, '2025-12-08', 6.0),
  (4, '2025-12-08', 12.5),
  (6, '2025-12-10', 7.0),
  (10, '2025-12-10', 11.0),
  (1, '2026-01-06', 10.5),
  (2, '2026-01-06', 12.0),
  (4, '2026-01-12', 16.0),
  (5, '2026-01-12', 5.5),
  (7, '2026-01-15', 6.5),
  (9, '2026-01-15', 8.0),
  (10, '2026-01-20', 14.0),
  (8, '2026-01-20', 4.0),
  (3, '2026-02-03', 7.5),
  (6, '2026-02-03', 9.0),
  (2, '2026-02-10', 8.5),
  (4, '2026-02-17', 13.0),
  (10, '2026-02-17', 10.5),
  (5, '2026-02-24', 4.0),
  (1, '2026-03-05', 6.0),
  (9, '2026-03-05', 6.5),
  (8, '2026-03-10', 3.0),
  (7, '2026-03-10', 4.5),
  (1, '2026-11-03', 6.5),
  (4, '2026-11-04', 9.0),
  (10, '2026-11-05', 7.5);

INSERT INTO ventas_cafe (fecha, comprador, quintales, precio_quintal) VALUES
  ('2025-12-12', 'Cooperativa Cafetalera Comayagua', 18.5, 7450.0),
  ('2026-01-09', 'Exportadora Santa Rosa', 32.0, 7820.0),
  ('2026-01-23', 'Beneficio Montecristo', 12.0, 7600.0),
  ('2026-02-06', 'Cooperativa Cafetalera Comayagua', 25.5, 7910.0),
  ('2026-02-27', 'Exportadora Santa Rosa', 40.0, 8120.0),
  ('2026-03-13', 'Beneficio Montecristo', 15.0, 8050.0),
  ('2026-04-03', 'Cooperativa Cafetalera Comayagua', 9.5, 8230.0),
  ('2026-05-08', 'Café Selecto de Honduras', 6.0, 8400.0),
  ('2026-07-17', 'Café Selecto de Honduras', 11.0, 8650.0),
  ('2026-10-02', 'Exportadora Santa Rosa', 7.5, 8890.0);

-- Usuario de prueba: admin / admin123 (cámbialo antes de entregar a producción)
INSERT INTO usuarios (usuario, nombre, password_hash) VALUES
  ('admin', 'Administrador', 'pbkdf2_sha256$200000$a3f1c8d20b7e4915c6d3e8f0124b9a77$8f39178f71621723e3fd3b3fa435e5e83e827bf40b677af36109f04ffe694213');
