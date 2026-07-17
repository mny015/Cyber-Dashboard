-- Store the note selected during approval separately from the topic-level request.
-- A request describes who asked for access to a topic; a grant records the one
-- note that the owner chose to share after approving that request.
CREATE TABLE IF NOT EXISTS note_access_grants (
    request_id INT NOT NULL,
    note_id INT NOT NULL,
    granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (request_id),
    KEY ix_note_access_grants_note_id (note_id),
    CONSTRAINT fk_note_access_grants_request
        FOREIGN KEY (request_id) REFERENCES note_access_requests(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_note_access_grants_note
        FOREIGN KEY (note_id) REFERENCES notes(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- Preserve existing approved selections before removing the derived note column.
INSERT INTO note_access_grants (request_id, note_id, granted_at)
SELECT id, note_id, COALESCE(responded_at, requested_at)
FROM note_access_requests
WHERE status = 'approved'
  AND note_id IS NOT NULL
ON DUPLICATE KEY UPDATE
    note_id = VALUES(note_id),
    granted_at = VALUES(granted_at);

SET @fk_name = (
    SELECT constraint_name
    FROM information_schema.key_column_usage
    WHERE table_schema = DATABASE()
      AND table_name = 'note_access_requests'
      AND column_name = 'note_id'
      AND referenced_table_name = 'notes'
    LIMIT 1
);
SET @migration_sql = IF(
    @fk_name IS NULL,
    'SELECT 1',
    CONCAT('ALTER TABLE note_access_requests DROP FOREIGN KEY `', @fk_name, '`')
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'note_access_requests'
      AND index_name = 'ix_note_access_note_id'
);
SET @migration_sql = IF(
    @index_exists = 0,
    'SELECT 1',
    'ALTER TABLE note_access_requests DROP INDEX ix_note_access_note_id'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'note_access_requests'
      AND column_name = 'note_id'
);
SET @migration_sql = IF(
    @column_exists = 0,
    'SELECT 1',
    'ALTER TABLE note_access_requests DROP COLUMN note_id'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
