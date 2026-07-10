-- User learning topics, optionally grouped under a category.
CREATE TABLE IF NOT EXISTS topics (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'planned',
    priority VARCHAR(40) NOT NULL DEFAULT 'medium',
    notes TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    category_id INT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_topic_owner_slug (owner_id, slug),
    KEY ix_topics_owner_id (owner_id),
    CONSTRAINT fk_topics_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_topics_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
