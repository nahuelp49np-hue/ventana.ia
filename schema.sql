-- ventana.ia / SYS.VENTANA
-- Schema SQLite — listo para migrar a Postgres más adelante.
-- Fechas en ISO-8601 (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS), zona del local.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('deposito', 'admin')),
    display_name  TEXT    NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sku               TEXT UNIQUE,
    name              TEXT    NOT NULL,
    category          TEXT    NOT NULL DEFAULT '',
    unit              TEXT    NOT NULL DEFAULT 'un',
    default_life_days INTEGER,
    notes             TEXT    NOT NULL DEFAULT '',
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS intakes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_path       TEXT,
    supplier         TEXT    NOT NULL DEFAULT '',
    document_number  TEXT    NOT NULL DEFAULT '',
    document_date    TEXT,
    raw_ocr          TEXT,
    confidence       REAL,
    status           TEXT    NOT NULL DEFAULT 'borrador'
                     CHECK (status IN ('borrador', 'confirmado', 'descartado')),
    warnings         TEXT    NOT NULL DEFAULT '[]',
    created_by       INTEGER REFERENCES users(id),
    created_at       TEXT    NOT NULL,
    confirmed_at     TEXT
);

CREATE TABLE IF NOT EXISTS intake_lines (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id   INTEGER NOT NULL REFERENCES intakes(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id),
    raw_name    TEXT    NOT NULL,
    quantity    REAL    NOT NULL DEFAULT 1,
    unit        TEXT    NOT NULL DEFAULT 'un',
    expires_at  TEXT,
    notes       TEXT    NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS batches (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id       INTEGER REFERENCES products(id),
    intake_id        INTEGER REFERENCES intakes(id),
    intake_line_id   INTEGER REFERENCES intake_lines(id),
    display_name     TEXT    NOT NULL,
    sku              TEXT,
    category         TEXT    NOT NULL DEFAULT '',
    quantity_initial REAL    NOT NULL,
    quantity_current REAL    NOT NULL,
    unit             TEXT    NOT NULL DEFAULT 'un',
    received_at      TEXT    NOT NULL,
    expires_at       TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'activo'
                     CHECK (status IN ('activo', 'promocion', 'retirado', 'agotado')),
    notes            TEXT    NOT NULL DEFAULT '',
    created_by       INTEGER REFERENCES users(id),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id        INTEGER REFERENCES batches(id),
    user_id         INTEGER REFERENCES users(id),
    kind            TEXT    NOT NULL,
    quantity_before REAL,
    quantity_after  REAL,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER REFERENCES batches(id),
    level    TEXT    NOT NULL,
    channel  TEXT    NOT NULL,
    payload  TEXT    NOT NULL DEFAULT '',
    status   TEXT    NOT NULL DEFAULT 'enviado',
    sent_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_batches_expires ON batches(expires_at);
CREATE INDEX IF NOT EXISTS idx_batches_status  ON batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(product_id);
CREATE INDEX IF NOT EXISTS idx_actions_batch   ON actions(batch_id, created_at);
CREATE INDEX IF NOT EXISTS idx_alert_batch     ON alert_log(batch_id, level, sent_at);
CREATE INDEX IF NOT EXISTS idx_products_name   ON products(name);
CREATE INDEX IF NOT EXISTS idx_intake_lines    ON intake_lines(intake_id);
