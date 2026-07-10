-- Authentication, authorization, MFA, lockout, and profile data.
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(64) NULL,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    auth_version INT NOT NULL DEFAULT 0,
    failed_login_count INT NOT NULL DEFAULT 0,
    last_failed_login_at DATETIME NULL,
    locked_until DATETIME NULL,
    profile_bio TEXT NULL,
    profile_image CHAR(64) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    CONSTRAINT fk_users_profile_image
        FOREIGN KEY (profile_image) REFERENCES profile_images(image_hash)
) ENGINE=InnoDB;
