-- Normalized threat tactics and their default levels.
CREATE TABLE IF NOT EXISTS threat_catalog (
    id INT NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(200) NOT NULL,
    default_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    description TEXT NOT NULL,
    source VARCHAR(160) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_threat_code (code)
) ENGINE=InnoDB;
