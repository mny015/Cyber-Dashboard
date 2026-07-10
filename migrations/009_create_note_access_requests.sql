-- User-controlled approvals for an administrator to read one private note.
CREATE TABLE IF NOT EXISTS note_access_requests (
    id INT NOT NULL AUTO_INCREMENT,
    topic_id INT NOT NULL,
    note_id INT NULL,
    requester_admin_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_at DATETIME NOT NULL,
    responded_at DATETIME NULL,
    PRIMARY KEY (id),
    KEY ix_note_access_admin_id (requester_admin_id),
    KEY ix_note_access_topic_id (topic_id),
    KEY ix_note_access_note_id (note_id),
    CONSTRAINT fk_note_access_admin FOREIGN KEY (requester_admin_id) REFERENCES users(id),
    CONSTRAINT fk_note_access_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
    CONSTRAINT fk_note_access_note FOREIGN KEY (note_id) REFERENCES notes(id)
) ENGINE=InnoDB;
