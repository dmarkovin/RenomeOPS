-- ==========================
-- Renome OPS Database Schema
-- ==========================


-- Сотрудники
CREATE TABLE IF NOT EXISTS employees (

    id SERIAL PRIMARY KEY,

    telegram_id BIGINT UNIQUE,

    username VARCHAR(255),

    full_name VARCHAR(255) NOT NULL,

    phone VARCHAR(50),

    role VARCHAR(50) NOT NULL,

    team VARCHAR(50),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- Задачи
CREATE TABLE IF NOT EXISTS tasks (

    id SERIAL PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    created_by BIGINT,

    assigned_to BIGINT,

    priority VARCHAR(20) DEFAULT 'NORMAL',

    status VARCHAR(30) DEFAULT 'NEW',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMP
);



-- История задач
CREATE TABLE IF NOT EXISTS task_history (

    id SERIAL PRIMARY KEY,

    task_id INTEGER REFERENCES tasks(id)
        ON DELETE CASCADE,

    employee_id INTEGER REFERENCES employees(id)
        ON DELETE SET NULL,

    action TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- Доставки
CREATE TABLE IF NOT EXISTS deliveries (

    id SERIAL PRIMARY KEY,

    recipient VARCHAR(255),

    description TEXT,

    status VARCHAR(30) DEFAULT 'NEW',

    created_by INTEGER REFERENCES employees(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- Ключи
CREATE TABLE IF NOT EXISTS keys (

    id SERIAL PRIMARY KEY,

    key_name VARCHAR(255) NOT NULL,

    taken_by INTEGER REFERENCES employees(id),

    status VARCHAR(30) DEFAULT 'AVAILABLE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- Документы
CREATE TABLE IF NOT EXISTS documents (

    id SERIAL PRIMARY KEY,

    name VARCHAR(255) NOT NULL,

    file_id TEXT,

    uploaded_by INTEGER REFERENCES employees(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- Обходы
CREATE TABLE IF NOT EXISTS checklists (

    id SERIAL PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    status VARCHAR(30) DEFAULT 'NEW',

    created_by INTEGER REFERENCES employees(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
