-- fix_logros_complete.sql - Arreglar tablas de logros completamente
USE alfaia_db;

-- Verificar si la tabla logros existe, si no, crearla
CREATE TABLE IF NOT EXISTS logros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50) DEFAULT 'trophy',
    puntos_recompensa INT DEFAULT 0,
    tipo_logro ENUM('lectura', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 'general') DEFAULT 'general',
    rareza ENUM('comun', 'raro', 'epico', 'legendario') DEFAULT 'comun',
    condiciones JSON,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verificar si la tabla logros_desbloqueados existe, si no, crearla
CREATE TABLE IF NOT EXISTS logros_desbloqueados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    logro_id INT NOT NULL,
    fecha_desbloqueo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    puntos_obtenidos INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (logro_id) REFERENCES logros(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_logro (user_id, logro_id),
    INDEX idx_user_logros (user_id),
    INDEX idx_fecha_desbloqueo (fecha_desbloqueo)
);

-- Si la columna fecha_desbloqueo no existe, agregarla
ALTER TABLE logros_desbloqueados
ADD COLUMN IF NOT EXISTS fecha_desbloqueo TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Insertar algunos logros básicos si no existen
INSERT IGNORE INTO logros (nombre, descripcion, icono, puntos_recompensa, tipo_logro, rareza) VALUES
('Primer Paso', 'Completaste tu primer ejercicio', 'star', 10, 'general', 'comun'),
('Lector Principiante', 'Completaste 5 ejercicios de lectura', 'book', 25, 'lectura', 'comun'),
('Pronunciación Clara', 'Logró 90% de precisión en pronunciación', 'microphone', 30, 'pronunciacion', 'raro'),
('Memoria de Acero', 'Completó un juego de memoria sin errores', 'brain', 35, 'memoria', 'raro'),
('Detective de Palabras', 'Resolvió 10 ahorcados consecutivos', 'search', 40, 'ahorcado', 'epico'),
('Genio del Conocimiento', 'Puntuación perfecta en trivia', 'graduation-cap', 50, 'trivia', 'epico'),
('Maestro del Alfabeto', 'Completó ejercicios en todas las categorías', 'crown', 100, 'general', 'legendario');

-- Verificar que las columnas existan en la estructura actual
DESCRIBE logros_desbloqueados;