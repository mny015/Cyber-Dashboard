-- Historical daily activity events retained for metrics data compatibility.
CREATE TABLE IF NOT EXISTS activity_events (
    id INT NOT NULL AUTO_INCREMENT,
    event_type VARCHAR(80) NOT NULL,
    intensity INT NOT NULL,
    occurred_on DATE NOT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_activity_events_owner_id (owner_id),
    CONSTRAINT fk_activity_events_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
