USE pool_db;

CREATE TABLE customers (
  customer_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  first_name  VARCHAR(60) NOT NULL,
  last_name   VARCHAR(60) NOT NULL,
  phone       VARCHAR(30),
  email       VARCHAR(120),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_customers_email (email)
) ENGINE=InnoDB;

CREATE TABLE properties (
  property_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,
  label       VARCHAR(80) NOT NULL,
  address1    VARCHAR(120) NOT NULL,
  address2    VARCHAR(120),
  city        VARCHAR(80),
  state       VARCHAR(80),
  postal_code VARCHAR(20),
  notes       TEXT,
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_properties_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE pools (
  pool_id     BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  property_id BIGINT UNSIGNED NOT NULL,
  label       VARCHAR(80) NOT NULL,
  pool_type   ENUM('pool','spa','both') NOT NULL DEFAULT 'pool',
  surface     ENUM('plaster','tile','vinyl','fiberglass','other') DEFAULT 'other',
  notes       TEXT,
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_pools_property
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE technicians (
  technician_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(120) NOT NULL,
  phone         VARCHAR(30),
  email         VARCHAR(120),
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_technicians_email (email)
) ENGINE=InnoDB;

CREATE TABLE service_plans (
  plan_id      BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  plan_name    VARCHAR(80) NOT NULL,
  frequency    ENUM('weekly') NOT NULL DEFAULT 'weekly',
  base_price   DECIMAL(10,2) NOT NULL,
  description  TEXT,
  is_active    TINYINT(1) NOT NULL DEFAULT 1,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_service_plans_name (plan_name)
) ENGINE=InnoDB;

CREATE TABLE property_plans (
  property_plan_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  property_id      BIGINT UNSIGNED NOT NULL,
  plan_id          BIGINT UNSIGNED NOT NULL,
  start_date       DATE NOT NULL,
  end_date         DATE NULL,
  status           ENUM('active','paused','ended') NOT NULL DEFAULT 'active',
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_property_plans_property
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_property_plans_plan
    FOREIGN KEY (plan_id) REFERENCES service_plans(plan_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE visits (
  visit_id      BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  property_id   BIGINT UNSIGNED NOT NULL,
  pool_id       BIGINT UNSIGNED NULL,
  technician_id BIGINT UNSIGNED NULL,
  visit_date    DATE NOT NULL,
  status        ENUM('scheduled','completed','skipped','canceled') NOT NULL DEFAULT 'completed',
  notes         TEXT,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_visits_property
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_visits_pool
    FOREIGN KEY (pool_id) REFERENCES pools(pool_id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_visits_technician
    FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE service_catalog (
  service_id   BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  service_name VARCHAR(80) NOT NULL,
  default_fee  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  is_active    TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uq_service_catalog_name (service_name)
) ENGINE=InnoDB;

CREATE TABLE visit_services (
  visit_service_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  visit_id         BIGINT UNSIGNED NOT NULL,
  service_id       BIGINT UNSIGNED NOT NULL,
  quantity         DECIMAL(10,2) NOT NULL DEFAULT 1.00,
  fee              DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  notes            VARCHAR(255),
  CONSTRAINT fk_visit_services_visit
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_visit_services_service
    FOREIGN KEY (service_id) REFERENCES service_catalog(service_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE invoices (
  invoice_id   BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  customer_id  BIGINT UNSIGNED NOT NULL,
  property_id  BIGINT UNSIGNED NOT NULL,
  period_start DATE NOT NULL,
  period_end   DATE NOT NULL,
  status       ENUM('draft','sent','paid','void') NOT NULL DEFAULT 'sent',
  issued_date  DATE NOT NULL,
  due_date     DATE NULL,
  subtotal     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  tax          DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  total        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  notes        TEXT,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_invoices_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_invoices_property
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE invoice_lines (
  invoice_line_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  invoice_id      BIGINT UNSIGNED NOT NULL,
  description     VARCHAR(160) NOT NULL,
  quantity        DECIMAL(10,2) NOT NULL DEFAULT 1.00,
  unit_price      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  line_total      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  CONSTRAINT fk_invoice_lines_invoice
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payments (
  payment_id  BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  invoice_id  BIGINT UNSIGNED NOT NULL,
  paid_date   DATE NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  method      ENUM('cash','ath_movil','card','bank_transfer','check','other') NULL DEFAULT 'other',
  reference   VARCHAR(80),
  notes       VARCHAR(255),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_payments_invoice
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_properties_customer ON properties(customer_id);
CREATE INDEX idx_pools_property ON pools(property_id);

CREATE INDEX idx_property_plans_property ON property_plans(property_id);
CREATE INDEX idx_property_plans_plan ON property_plans(plan_id);
CREATE INDEX idx_property_plans_dates ON property_plans(start_date, end_date);

CREATE INDEX idx_visits_property_date ON visits(property_id, visit_date);
CREATE INDEX idx_visits_date ON visits(visit_date);

CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_property_period ON invoices(property_id, period_start, period_end);
CREATE INDEX idx_invoices_status ON invoices(status);
