-- Historical learning roadmap milestones retained for data compatibility.
CREATE TABLE IF NOT EXISTS roadmap_items (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    milestone VARCHAR(120) NOT NULL,
    status VARCHAR(40) NOT NULL,
    due_date DATE NULL,
    topic_id INT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_roadmap_items_topic_id (topic_id),
    KEY ix_roadmap_items_owner_id (owner_id),
    CONSTRAINT fk_roadmap_items_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
    CONSTRAINT fk_roadmap_items_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
