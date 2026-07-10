-- Normalized names and slugs for external practice platforms.
CREATE TABLE IF NOT EXISTS lab_platforms (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_lab_platform_name (name),
    UNIQUE KEY uq_lab_platform_slug (slug)
) ENGINE=InnoDB;
