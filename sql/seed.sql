-- Demo seed data for Ektor Pool Services API
-- IMPORTANT: set your DB name below
-- USE Ektor_Pool_Services;

-- Optional: clear tables (ONLY for demo/dev environments)
-- If you have foreign keys, deleting in this order helps avoid constraint errors.
DELETE FROM invoices;
DELETE FROM properties;
DELETE FROM customers;

-- Reset auto-increment (MySQL)
ALTER TABLE invoices AUTO_INCREMENT = 1;
ALTER TABLE properties AUTO_INCREMENT = 1;
ALTER TABLE customers AUTO_INCREMENT = 1;

-- -----------------------
-- Customers (2 demo rows)
-- -----------------------
INSERT INTO customers (first_name, last_name, phone, email)
VALUES
('Ektor', 'Gonzalez', '787-000-0000', 'ektor.demo1@example.com'),
('Maria', 'Lopez',   '787-111-1111', 'maria.demo2@example.com');

-- -----------------------
-- Properties (2 demo rows)
-- Assumes customer_id = 1 and 2 due to reset above
-- -----------------------
INSERT INTO properties (customer_id, label, address1, address2, city, state, postal_code, notes, is_active)
VALUES
(1, 'Home Pool',     '123 Beach Rd', NULL,  'Rincon',    'PR', '00677', 'Weekly service',   1),
(2, 'Rental Villa',  '45 Sunset Ave','Unit B','Aguadilla','PR', '00603', 'Bi-weekly service',1);

-- -----------------------
-- Invoices (2 demo rows)
-- Assumes property_id = 1 and 2 due to reset above
-- -----------------------
INSERT INTO invoices
(customer_id, property_id, period_start, period_end, status, issued_date, due_date, subtotal, tax, total, notes)
VALUES
(1, 1, '2026-01-01', '2026-01-07', 'sent', '2026-01-07', '2026-01-14', 100.00, 10.00, 110.00, 'Weekly billing'),
(2, 2, '2026-01-01', '2026-01-15', 'paid', '2026-01-15', '2026-01-15', 180.00, 18.00, 198.00, 'Bi-weekly service');
