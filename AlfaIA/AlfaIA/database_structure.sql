-- =========================================
-- BASE DE DATOS ALFAIA - VERSIÓN CORREGIDA
-- =========================================

-- 1. Crear la base de datos ALFAIA
DROP DATABASE IF EXISTS alfaia;
CREATE DATABASE alfaia
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE alfaia;

-- 2. Crear usuario específico para la aplicación (opcional pero recomendado)
-- DROP USER IF EXISTS 'alfaia_user'@'localhost';
-- CREATE USER 'alfaia_user'@'localhost' IDENTIFIED BY 'alfaia_password_2024';
-- GRANT ALL PRIVILEGES ON alfaia.* TO 'alfaia_user'@'localhost';
-- FLUSH PRIVILEGES;

-- =========================================
-- TABLAS PRINCIPALES
-- =========================================

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
    activo BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,

    -- Índices
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de ejercicios realizados
CREATE TABLE ejercicios_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo_ejercicio ENUM('lectura', 'ejercicios', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 'crucigrama') NOT NULL,
    nombre_ejercicio VARCHAR(100) NOT NULL,
    puntos_obtenidos INT DEFAULT 0,
    precision_porcentaje DECIMAL(5,2) DEFAULT 0.00,
    tiempo_empleado_segundos INT DEFAULT 0,
    fecha_completado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    datos_adicionales JSON,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_fecha (usuario_id, fecha_completado),
    INDEX idx_tipo (tipo_ejercicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de logros
CREATE TABLE logros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_logro VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50) DEFAULT '🏆',
    categoria ENUM('ejercicios', 'pronunciacion', 'racha', 'precision', 'especial') DEFAULT 'ejercicios',
    fecha_obtenido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_logro (usuario_id, nombre_logro),
    INDEX idx_usuario (usuario_id),
    INDEX idx_categoria (categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de vocales detectadas
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
    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_realizados(id) ON DELETE SET NULL,
    INDEX idx_usuario (usuario_id),
    INDEX idx_vocal (vocal),
    INDEX idx_fecha (fecha_deteccion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de configuraciones del usuario
CREATE TABLE configuraciones_usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    velocidad_lectura INT DEFAULT 500,
    dificultad_preferida ENUM('facil', 'medio', 'dificil') DEFAULT 'medio',
    tema_preferido VARCHAR(50) DEFAULT 'brown',
    notificaciones_activas BOOLEAN DEFAULT TRUE,
    sonidos_activos BOOLEAN DEFAULT TRUE,
    configuracion_json JSON,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_config (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de sesiones
CREATE TABLE sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP,
    activa BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_usuario_activa (usuario_id, activa),
    INDEX idx_expiracion (fecha_expiracion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de estadísticas diarias
CREATE TABLE estadisticas_diarias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha DATE NOT NULL,
    ejercicios_completados INT DEFAULT 0,
    tiempo_estudiado_minutos INT DEFAULT 0,
    puntos_obtenidos INT DEFAULT 0,
    precision_promedio DECIMAL(5,2) DEFAULT 0.00,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (usuario_id, fecha),
    INDEX idx_usuario_fecha (usuario_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================
-- PROCEDIMIENTOS ALMACENADOS
-- =========================================

DELIMITER //

CREATE PROCEDURE ActualizarEstadisticasUsuario(
    IN p_usuario_id INT,
    IN p_puntos INT,
    IN p_precision DECIMAL(5,2),
    IN p_tiempo_segundos INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Actualizar progreso general
    UPDATE progreso_usuario
    SET
        ejercicios_completados = ejercicios_completados + 1,
        tiempo_total_minutos = tiempo_total_minutos + CEIL(p_tiempo_segundos / 60),
        puntos_totales = puntos_totales + p_puntos,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE usuario_id = p_usuario_id;

    -- Si no existe el registro de progreso, crearlo
    INSERT IGNORE INTO progreso_usuario (usuario_id) VALUES (p_usuario_id);

    -- Actualizar precisión promedio
    UPDATE progreso_usuario p
    SET precision_promedio = (
        SELECT AVG(precision_porcentaje)
        FROM ejercicios_realizados
        WHERE usuario_id = p_usuario_id
    )
    WHERE p.usuario_id = p_usuario_id;

    -- Actualizar estadísticas diarias
    INSERT INTO estadisticas_diarias
        (usuario_id, fecha, ejercicios_completados, tiempo_estudiado_minutos, puntos_obtenidos, precision_promedio)
    VALUES
        (p_usuario_id, CURDATE(), 1, CEIL(p_tiempo_segundos / 60), p_puntos, p_precision)
    ON DUPLICATE KEY UPDATE
        ejercicios_completados = ejercicios_completados + 1,
        tiempo_estudiado_minutos = tiempo_estudiado_minutos + CEIL(p_tiempo_segundos / 60),
        puntos_obtenidos = puntos_obtenidos + p_puntos,
        precision_promedio = (precision_promedio + p_precision) / 2;

    COMMIT;
END //

CREATE PROCEDURE VerificarLogros(IN p_usuario_id INT)
BEGIN
    DECLARE total_ejercicios INT DEFAULT 0;
    DECLARE precision_promedio DECIMAL(5,2) DEFAULT 0;
    DECLARE racha_dias INT DEFAULT 0;
    DECLARE total_vocales INT DEFAULT 0;

    -- Obtener estadísticas del usuario
    SELECT
        COALESCE(ejercicios_completados, 0),
        COALESCE(progreso_usuario.precision_promedio, 0),
        COALESCE(racha_dias, 0)
    INTO total_ejercicios, precision_promedio, racha_dias
    FROM progreso_usuario
    WHERE usuario_id = p_usuario_id;

    -- Contar total de vocales detectadas
    SELECT COUNT(*) INTO total_vocales
    FROM vocales_detectadas
    WHERE usuario_id = p_usuario_id;

    -- Logros automáticos

    -- Primer ejercicio
    IF total_ejercicios >= 1 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Primer Paso', 'Completaste tu primer ejercicio', '🌟', 'ejercicios');
    END IF;

    -- 10 ejercicios
    IF total_ejercicios >= 10 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Estudiante Dedicado', 'Completaste 10 ejercicios', '📚', 'ejercicios');
    END IF;

    -- 50 ejercicios
    IF total_ejercicios >= 50 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Maestro del Aprendizaje', 'Completaste 50 ejercicios', '🎓', 'ejercicios');
    END IF;

    -- Racha de 7 días
    IF racha_dias >= 7 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Una Semana Completa', 'Practicaste 7 días seguidos', '🔥', 'racha');
    END IF;

    -- Precisión alta
    IF precision_promedio >= 95.00 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Perfeccionista', 'Mantuviste 95% de precisión promedio', '💯', 'precision');
    END IF;

    -- Maestro de vocales
    IF total_vocales >= 100 THEN
        INSERT IGNORE INTO logros (usuario_id, nombre_logro, descripcion, icono, categoria)
        VALUES (p_usuario_id, 'Maestro de Vocales', 'Detectaste 100 vocales en total', '🗣️', 'pronunciacion');
    END IF;

END //

DELIMITER ;

-- =========================================
-- DATOS INICIALES
-- =========================================

-- Usuario demo (contraseña: demo123)
INSERT INTO usuarios (username, email, password_hash, nombre, apellido, fecha_nacimiento, is_admin) VALUES
('demo_user', 'demo@alfaia.com', '$2b$12$LQv3c1yqBwfN9RfBgT.OseEEWEOhUiUwLIaqklB6jQk0sn8O3RWIG', 'Usuario', 'Demo', '1990-01-01', FALSE),
('admin', 'admin@alfaia.com', '$2b$12$LQv3c1yqBwfN9RfBgT.OseEEWEOhUiUwLIaqklB6jQk0sn8O3RWIG', 'Administrador', 'Sistema', '1985-01-01', TRUE);

-- Progreso inicial para usuarios
INSERT INTO progreso_usuario (usuario_id) VALUES (1), (2);

-- Configuraciones iniciales
INSERT INTO configuraciones_usuario (usuario_id) VALUES (1), (2);

-- Algunos ejercicios de ejemplo para el usuario demo
INSERT INTO ejercicios_realizados (usuario_id, tipo_ejercicio, nombre_ejercicio, puntos_obtenidos, precision_porcentaje, tiempo_empleado_segundos) VALUES
(1, 'lectura', 'Lectura Guiada', 25, 85.50, 120),
(1, 'ejercicios', 'Ordenar Frases', 30, 92.00, 95),
(1, 'pronunciacion', 'Detección de Vocales', 20, 78.00, 60);

-- Estadísticas diarias de ejemplo
INSERT INTO estadisticas_diarias (usuario_id, fecha, ejercicios_completados, tiempo_estudiado_minutos, puntos_obtenidos, precision_promedio) VALUES
(1, CURDATE(), 3, 5, 75, 85.17),
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2, 3, 50, 88.50);

-- Ejecutar verificación de logros para el usuario demo
CALL VerificarLogros(1);

-- =========================================
-- VERIFICACIONES FINALES
-- =========================================

-- Mostrar información de las tablas creadas
SELECT 'Tablas creadas exitosamente:' AS mensaje;
SHOW TABLES;

-- Verificar usuario demo
SELECT 'Usuario demo creado:' AS mensaje;
SELECT id, username, email, nombre, apellido, activo FROM usuarios WHERE username = 'demo_user';

-- Verificar progreso del usuario demo
SELECT 'Progreso del usuario demo:' AS mensaje;
SELECT * FROM progreso_usuario WHERE usuario_id = 1;

-- Verificar logros del usuario demo
SELECT 'Logros del usuario demo:' AS mensaje;
SELECT nombre_logro, descripcion, icono, fecha_obtenido FROM logros WHERE usuario_id = 1;

COMMIT;
