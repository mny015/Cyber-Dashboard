-- User or administrator lab links, linked to a platform and optional topic.
CREATE TABLE IF NOT EXISTS lab_references (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    platform_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,
    notes TEXT NOT NULL,
    topic_id INT NULL,
    owner_id INT NOT NULL,
    visibility VARCHAR(20) NOT NULL DEFAULT 'personal',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_lab_references_owner_id (owner_id),
    KEY ix_lab_references_topic_id (topic_id),
    KEY ix_lab_references_platform_id (platform_id),
    CONSTRAINT fk_lab_references_owner FOREIGN KEY (owner_id) REFERENCES users(id),
    CONSTRAINT fk_lab_references_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
    CONSTRAINT fk_lab_references_platform FOREIGN KEY (platform_id) REFERENCES lab_platforms(id)
) ENGINE=InnoDB;
