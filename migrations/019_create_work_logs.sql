-- Historical VAPT/GRC work-log records retained for data compatibility.
CREATE TABLE IF NOT EXISTS work_logs (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    log_type VARCHAR(40) NOT NULL,
    content TEXT NOT NULL,
    evidence_url VARCHAR(255) NOT NULL,
    risk_rating VARCHAR(40) NOT NULL,
    log_date DATE NOT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_work_logs_owner_id (owner_id),
    CONSTRAINT fk_work_logs_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
