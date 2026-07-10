-- Private contact records owned by individual users.
CREATE TABLE IF NOT EXISTS contacts (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(40) NOT NULL,
    notes TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    owner_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_contacts_owner_id (owner_id),
    CONSTRAINT fk_contacts_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB;
