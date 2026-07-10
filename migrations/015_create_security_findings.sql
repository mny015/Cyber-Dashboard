-- User-owned vulnerability tests, detected threats, and managed findings.
CREATE TABLE IF NOT EXISTS security_findings (
    id INT NOT NULL AUTO_INCREMENT,
    owner_id INT NOT NULL,
    vulnerability_id INT NULL,
    threat_id INT NULL,
    activity_type VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    target VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    evidence TEXT NOT NULL,
    notes TEXT NOT NULL,
    detected_at DATETIME NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_security_findings_owner_id (owner_id),
    KEY ix_security_findings_vulnerability_id (vulnerability_id),
    KEY ix_security_findings_threat_id (threat_id),
    CONSTRAINT fk_security_findings_owner FOREIGN KEY (owner_id) REFERENCES users(id),
    CONSTRAINT fk_security_findings_vulnerability
        FOREIGN KEY (vulnerability_id) REFERENCES vulnerability_catalog(id),
    CONSTRAINT fk_security_findings_threat FOREIGN KEY (threat_id) REFERENCES threat_catalog(id)
) ENGINE=InnoDB;
