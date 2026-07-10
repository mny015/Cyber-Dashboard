-- Deduplicated, validated user profile images stored outside the static folder.
CREATE TABLE IF NOT EXISTS profile_images (
    image_hash CHAR(64) NOT NULL,
    image_data LONGBLOB NOT NULL,
    mime_type VARCHAR(80) NOT NULL,
    byte_size INT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (image_hash)
) ENGINE=InnoDB;
