-- Система учёта расходов организации: проверенные SQL-запросы.
-- Числа и строки в демонстрационных запросах нужны для ручной проверки.
-- В Django-страницах пользовательские значения всегда передаются через ?.

-- 1. Полный список расходов со связанными категорией, подразделением и документом.
SELECT
    e.id,
    e.amount,
    c.name AS category_name,
    d.name AS department_name,
    doc.number AS document_number
FROM expenses AS e
JOIN categories AS c ON c.id = e.category_id
JOIN departments AS d ON d.id = e.department_id
JOIN documents AS doc ON doc.id = e.document_id
ORDER BY e.id;

-- 2. Список расходов от большей суммы к меньшей.
SELECT id, amount
FROM expenses
ORDER BY amount DESC, id;

-- 3. Поиск расходов на сумму не менее 10000 рублей.
SELECT id, amount
FROM expenses
WHERE amount >= 10000
ORDER BY amount DESC;

-- 4. Поиск расходов выбранной категории (пример: категория с ID 1).
SELECT e.id, e.amount, c.name AS category_name
FROM expenses AS e
JOIN categories AS c ON c.id = e.category_id
WHERE c.id = 1
ORDER BY e.amount DESC;

-- 5. Поиск расходов выбранного подразделения (пример: подразделение с ID 1).
SELECT e.id, e.amount, d.name AS department_name
FROM expenses AS e
JOIN departments AS d ON d.id = e.department_id
WHERE d.id = 1
ORDER BY e.id;

-- 6. Поиск расходов по номеру документа.
SELECT e.id, e.amount, doc.number AS document_number
FROM expenses AS e
JOIN documents AS doc ON doc.id = e.document_id
WHERE doc.number LIKE '%101%'
ORDER BY e.id;

-- 7. Расходы вместе с номером подтверждающего документа.
SELECT e.id, e.amount, doc.number AS document_number
FROM expenses AS e
JOIN documents AS doc ON doc.id = e.document_id
ORDER BY doc.number;

-- 8. Общая сумма, средняя сумма и количество расходов.
SELECT
    COUNT(*) AS expense_count,
    COALESCE(SUM(amount), 0) AS total_amount,
    COALESCE(AVG(amount), 0) AS average_amount
FROM expenses;

-- 9. Минимальная и максимальная сумма расхода.
SELECT
    COALESCE(MIN(amount), 0) AS min_amount,
    COALESCE(MAX(amount), 0) AS max_amount
FROM expenses;

-- 10. Количество и общая сумма расходов по категориям, включая пустые категории.
SELECT
    c.id,
    c.name AS category_name,
    COUNT(e.id) AS expense_count,
    COALESCE(SUM(e.amount), 0) AS total_amount
FROM categories AS c
LEFT JOIN expenses AS e ON e.category_id = c.id
GROUP BY c.id, c.name
ORDER BY total_amount DESC, c.name;

-- 11. Количество и общая сумма расходов по подразделениям.
SELECT
    d.id,
    d.name AS department_name,
    COUNT(e.id) AS expense_count,
    COALESCE(SUM(e.amount), 0) AS total_amount
FROM departments AS d
LEFT JOIN expenses AS e ON e.department_id = d.id
GROUP BY d.id, d.name
ORDER BY total_amount DESC, d.name;

-- 12. Общая сумма расходов по документам.
SELECT
    doc.number AS document_number,
    COUNT(e.id) AS expense_count,
    COALESCE(SUM(e.amount), 0) AS total_amount
FROM documents AS doc
LEFT JOIN expenses AS e ON e.document_id = doc.id
GROUP BY doc.id, doc.number
ORDER BY total_amount DESC, doc.number;

-- 13. Категории, по которым потрачено более 10000 рублей (HAVING).
SELECT
    c.name AS category_name,
    COUNT(e.id) AS expense_count,
    SUM(e.amount) AS total_amount
FROM categories AS c
JOIN expenses AS e ON e.category_id = c.id
GROUP BY c.id, c.name
HAVING SUM(e.amount) > 10000
ORDER BY total_amount DESC;

-- 14. Подразделения с расходами на сумму не менее 10000 рублей (HAVING).
SELECT
    d.name AS department_name,
    COUNT(e.id) AS expense_count,
    SUM(e.amount) AS total_amount
FROM departments AS d
JOIN expenses AS e ON e.department_id = d.id
GROUP BY d.id, d.name
HAVING SUM(e.amount) >= 10000
ORDER BY total_amount DESC;

-- 15. Категории, по которым пока не зарегистрировано расходов.
SELECT c.id, c.name
FROM categories AS c
LEFT JOIN expenses AS e ON e.category_id = c.id
WHERE e.id IS NULL
ORDER BY c.name;
