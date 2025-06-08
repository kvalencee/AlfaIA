-- Crear base de datos
CREATE DATABASE IF NOT EXISTS alfaia_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE alfaia_db;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE,
    nivel_actual INT DEFAULT 1,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de progreso del usuario
CREATE TABLE progreso_usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ejercicios_completados INT DEFAULT 0,
    tiempo_total_minutos INT DEFAULT 0,
    precision_promedio DECIMAL(5,2) DEFAULT 0.00,
    racha_dias INT DEFAULT 0,
    puntos_totales INT DEFAULT 0,
    nivel_lectura INT DEFAULT 1,
    nivel_ejercicios INT DEFAULT 1,
    nivel_pronunciacion INT DEFAULT 1,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de ejercicios realizados
CREATE TABLE ejercicios_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo_ejercicio ENUM('lectura', 'ejercicios', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 'crucigrama') NOT NULL,
    nombre_ejercicio VARCHAR(100) NOT NULL,
    puntos_obtenidos INT DEFAULT 0,
    precision DECIMAL(5,2) DEFAULT 0.00,
    tiempo_empleado INT DEFAULT 0, -- en segundos
    fecha_completado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    datos_adicionales JSON, -- para guardar datos específicos del ejercicio
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de logros
CREATE TABLE logros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_logro VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50),
    fecha_obtenido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de vocales detectadas (para pronunciación)
CREATE TABLE vocales_detectadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ejercicio_id INT,
    vocal CHAR(1) NOT NULL,
    frecuencia DECIMAL(8,2),
    tiempo_deteccion DECIMAL(5,2),
    confianza DECIMAL(5,2),
    fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_realizados(id) ON DELETE SET NULL
);

-- Tabla de configuraciones del usuario
CREATE TABLE configuraciones_usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    velocidad_lectura INT DEFAULT 500, -- milisegundos entre palabras
    dificultad_preferida ENUM('facil', 'medio', 'dificil') DEFAULT 'medio',
    tema_preferido VARCHAR(50) DEFAULT 'brown',
    notificaciones_activas BOOLEAN DEFAULT TRUE,
    sonidos_activos BOOLEAN DEFAULT TRUE,
    configuracion_json JSON, -- para configuraciones adicionales
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_config (usuario_id)
);

-- Tabla de sesiones (para manejar login)
CREATE TABLE sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP,
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de estadísticas diarias
CREATE TABLE estadisticas_diarias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha DATE NOT NULL,
    ejercicios_completados INT DEFAULT 0,
    tiempo_estudiado INT DEFAULT 0, -- en minutos
    puntos_obtenidos INT DEFAULT 0,
    precision_promedio DECIMAL(5,2) DEFAULT 0.00,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (usuario_id, fecha)
);

-- Índices para optimización
CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_ejercicios_usuario_fecha ON ejercicios_realizados(usuario_id, fecha_completado);
CREATE INDEX idx_ejercicios_tipo ON ejercicios_realizados(tipo_ejercicio);
CREATE INDEX idx_progreso_usuario ON progreso_usuario(usuario_id);
CREATE INDEX idx_sesiones_token ON sesiones(token);
CREATE INDEX idx_sesiones_usuario_activa ON sesiones(usuario_id, activa);
CREATE INDEX idx_estadisticas_usuario_fecha ON estadisticas_diarias(usuario_id, fecha);

-- Procedimientos almacenados útiles
DELIMITER //

-- Procedimiento para actualizar estadísticas del usuario
CREATE PROCEDURE ActualizarEstadisticasUsuario(
    IN p_usuario_id INT,
    IN p_puntos INT,
    IN p_precision DECIMAL(5,2),
    IN p_tiempo_segundos INT
)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE avg_precision DECIMAL(5,2);
    DECLARE total_ejercicios INT;

    -- Actualizar progreso general
    UPDATE progreso_usuario
    SET
        ejercicios_completados = ejercicios_completados + 1,
        tiempo_total_minutos = tiempo_total_minutos + CEIL(p_tiempo_segundos / 60),
        puntos_totales = puntos_totales + p_puntos,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE usuario_id = p_usuario_id;

    -- Calcular nueva precisión promedio
    SELECT
        AVG(precision),
        COUNT(*)
    INTO avg_precision, total_ejercicios
    FROM ejercicios_realizados
    WHERE usuario_id = p_usuario_id;

    -- Actualizar precisión promedio
    UPDATE progreso_usuario
    SET precision_promedio = COALESCE(avg_precision, 0)
    WHERE usuario_id = p_usuario_id;

    -- Actualizar estadísticas diarias
    INSERT INTO estadisticas_diarias
        (usuario_id, fecha, ejercicios_completados, tiempo_estudiado, puntos_obtenidos, precision_promedio)
    VALUES
        (p_usuario_id, CURDATE(), 1, CEIL(p_tiempo_segundos / 60), p_puntos, p_precision)
    ON DUPLICATE KEY UPDATE
        ejercicios_completados = ejercicios_completados + 1,
        tiempo_estudiado = tiempo_estudiado + CEIL(p_tiempo_segundos / 60),
        puntos_obtenidos = puntos_obtenidos + p_puntos,
        precision_promedio = (precision_promedio + p_precision) / 2;

END //

-- Procedimiento para verificar y otorgar logros
CREATE PROCEDURE VerificarLogros(IN p_usuario_id INT)
BEGIN
    DECLARE total_ejercicios INT;
    DECLARE precision_promedio DECIMAL(5,2);
    DECLARE racha_dias INT;
    DECLARE total_vocales INT;

    -- Obtener estadísticas del usuario
    SELECT
        ejercicios_completados,
        progreso_usuario.precision_promedio,
        racha_dias
    INTO total_ejercicios, precision_promedio, racha_dias
    FROM progreso_usuario
    WHERE usuario_id = p_usuario_id;

    -- Contar total de vocales detectadas
    SELECT COUNT(*) INTO total_vocales
    FROM vocales_detectadas
    WHERE usuario_id = p_usuario_id;

    -- Logro: Primer ejercicio
    IF total_ejercicios >= 1 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Primer Paso', 'Completaste tu primer ejercicio', '🌟');
    END IF;

    -- Logro: 10 ejercicios
    IF total_ejercicios >= 10 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Estudiante Dedicado', 'Completaste 10 ejercicios', '📚');
    END IF;

    -- Logro: 50 ejercicios
    IF total_ejercicios >= 50 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Maestro del Aprendizaje', 'Completaste 50 ejercicios', '🎓');
    END IF;

    -- Logro: Racha de 7 días
    IF racha_dias >= 7 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Una Semana Completa', 'Practicaste 7 días seguidos', '🔥');
    END IF;

    -- Logro: Precisión alta
    IF precision_promedio >= 95.00 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Perfeccionista', 'Mantuviste 95% de precisión promedio', '💯');
    END IF;

    -- Logro: Maestro de vocales
    IF total_vocales >= 100 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono)
        VALUES (p_usuario_id, 'Maestro de Vocales', 'Detectaste 100 vocales en total', '🗣️');
    END IF;

END //

DELIMITER ;

-- Insertar datos de ejemplo (opcional)
INSERT INTO usuarios (username, email, password_hash, nombre, apellido, fecha_nacimiento) VALUES
('demo_user', 'demo@alfaia.com', '$2b$12$LQv3c1yqBwfN9RfBgT.OseEEWEOhUiUwLIaqklB6jQk0sn8O3RWIG', 'Usuario', 'Demo', '1990-01-01');

-- Insertar progreso inicial para el usuario demo
INSERT INTO progreso_usuario (usuario_id) VALUES (1);

-- Insertar configuración inicial para el usuario demo
INSERT INTO configuraciones_usuario (usuario_id) VALUES (1);