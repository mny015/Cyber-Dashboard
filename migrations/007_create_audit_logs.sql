-- Security and accountability evidence for authentication and application actions.
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT NOT NULL AUTO_INCREMENT,
    action VARCHAR(120) NOT NULL,
    details TEXT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_id INT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_audit_logs_user_id (user_id),
    CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
