-- Personal assignments and administrator-created shared or user-specific work.
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NULL,
    created_by INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    task_type VARCHAR(40) NOT NULL DEFAULT 'general',
    due_at DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'upcoming',
    scope VARCHAR(20) NOT NULL DEFAULT 'personal',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_scheduled_tasks_user_id (user_id),
    KEY ix_scheduled_tasks_created_by (created_by),
    KEY ix_scheduled_tasks_scope_status (scope, status),
    CONSTRAINT fk_scheduled_tasks_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_scheduled_tasks_created_by FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;
