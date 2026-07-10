-- User-owned categories used to organize learning topics.
CREATE TABLE IF NOT EXISTS categories (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    color VARCHAR(32) NOT NULL DEFAULT '#2563eb',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_category_owner_name (owner_id, name),
    KEY ix_categories_owner_id (owner_id),
    CONSTRAINT fk_categories_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
