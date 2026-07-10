-- Private markdown notes owned by users and optionally linked to topics.
CREATE TABLE IF NOT EXISTS notes (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    topic_id INT NULL,
    owner_id INT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_notes_owner_id (owner_id),
    KEY ix_notes_topic_id (topic_id),
    CONSTRAINT fk_notes_owner FOREIGN KEY (owner_id) REFERENCES users(id),
    CONSTRAINT fk_notes_topic FOREIGN KEY (topic_id) REFERENCES topics(id)
) ENGINE=InnoDB;
