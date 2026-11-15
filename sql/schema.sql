-- Система учёта расходов организации: структура SQLite.

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    number TEXT NOT NULL UNIQUE CHECK (length(trim(number)) > 0)
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    amount REAL NOT NULL CHECK (amount >= 0),
    category_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_expenses_amount
    ON expenses(amount);
CREATE INDEX IF NOT EXISTS idx_expenses_category_id
    ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_department_id
    ON expenses(department_id);
CREATE INDEX IF NOT EXISTS idx_expenses_document_id
    ON expenses(document_id);
