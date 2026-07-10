-- One completion record per user and lab reference.
CREATE TABLE IF NOT EXISTS lab_completions (
    id INT NOT NULL AUTO_INCREMENT,
    lab_id INT NOT NULL,
    user_id INT NOT NULL,
    completed_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_lab_completion_user (lab_id, user_id),
    KEY ix_lab_completions_user_id (user_id),
    CONSTRAINT fk_lab_completions_lab FOREIGN KEY (lab_id) REFERENCES lab_references(id),
    CONSTRAINT fk_lab_completions_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
