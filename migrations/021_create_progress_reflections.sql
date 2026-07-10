-- Historical user reflection entries retained for data compatibility.
CREATE TABLE IF NOT EXISTS progress_reflections (
    id INT NOT NULL AUTO_INCREMENT,
    insight TEXT NOT NULL,
    challenge TEXT NOT NULL,
    next_step TEXT NOT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_progress_reflections_owner_id (owner_id),
    CONSTRAINT fk_progress_reflections_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
