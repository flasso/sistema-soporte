-- Crear tabla empresas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);

-- Insertar las empresas
INSERT INTO empresas (nombre) VALUES
('Acomedios'),
('Aldas'),
('Asoredes'),
('Big Media'),
('Cafam'),
('Century'),
('CNM'),
('Contructora de Marcas'),
('DORTIZ'),
('Elite'),
('Factorial'),
('Grupo One'),
('Zelva'),
('Integracion'),
('Inversiones CNM'),
('JH Hoyos'),
('Jaime Uribe'),
('Maproges'),
('Media Agency'),
('Media Plus'),
('Multimedios'),
('New Sapiens'),
('OMV'),
('Quintero y Quintero'),
('Servimedios'),
('Teleantioquia'),
('TBWA');

-- Crear tabla incidentes
CREATE TABLE IF NOT EXISTS incidentes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    telefono VARCHAR(50),
    empresa VARCHAR(100),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_problema VARCHAR(50),
    descripcion TEXT,
    estado VARCHAR(20) DEFAULT 'Abierto',
    respuesta TEXT,
    fecha_respuesta TIMESTAMP
);
