-- One-time, idempotent data normalization for databases created by older
-- project versions. Seed catalog data remains in scripts/seed.py.

-- The Python migration runner imports legacy profile files before this SQL runs.
-- Blob-backed rows are copied here as a second, database-only compatibility path.
SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'users'
       AND column_name = 'profile_image_data') = 1,
    'INSERT IGNORE INTO profile_images (image_hash, image_data, mime_type, byte_size, created_at) SELECT profile_image, profile_image_data, profile_image_mime, profile_image_size, NOW() FROM users WHERE profile_image_data IS NOT NULL AND CHAR_LENGTH(profile_image) = 64',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

ALTER TABLE users MODIFY profile_image CHAR(64) NULL;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'users'
       AND column_name = 'profile_image_data') = 1,
    'ALTER TABLE users DROP COLUMN profile_image_data',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'users'
       AND column_name = 'profile_image_mime') = 1,
    'ALTER TABLE users DROP COLUMN profile_image_mime',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'users'
       AND column_name = 'profile_image_size') = 1,
    'ALTER TABLE users DROP COLUMN profile_image_size',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

-- Empty legacy topic slugs receive deterministic, owner-safe values.
UPDATE topics
SET slug = CONCAT(
    LOWER(REPLACE(TRIM(title), ' ', '-')),
    '-',
    id
)
WHERE slug = '';

-- These five rows are required reference data for converting the old vendor
-- column. User-facing security catalog seeds are intentionally kept elsewhere.
INSERT INTO lab_platforms (name, slug)
VALUES
    ('picoCTF', 'picoctf'),
    ('TryHackMe', 'tryhackme'),
    ('Hack The Box', 'hack-the-box'),
    ('PortSwigger', 'portswigger'),
    ('Other', 'other')
ON DUPLICATE KEY UPDATE name = VALUES(name), slug = VALUES(slug);

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'lab_references'
       AND column_name = 'vendor') = 1,
    'INSERT IGNORE INTO lab_platforms (name, slug) SELECT DISTINCT vendor, LOWER(REPLACE(TRIM(vendor), '' '', ''-'')) FROM lab_references WHERE vendor IS NOT NULL AND vendor <> ''''',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'lab_references'
       AND column_name = 'vendor') = 1,
    'UPDATE lab_references AS labs JOIN lab_platforms AS platforms ON platforms.name = labs.vendor SET labs.platform_id = platforms.id WHERE labs.platform_id IS NULL',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE lab_references
SET platform_id = (SELECT id FROM lab_platforms WHERE slug = 'other')
WHERE platform_id IS NULL;

UPDATE lab_references
SET visibility = 'public'
WHERE visibility = 'everyone';

ALTER TABLE lab_references MODIFY platform_id INT NOT NULL;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'lab_references'
       AND column_name = 'vendor') = 1,
    'ALTER TABLE lab_references DROP COLUMN vendor',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

-- The owner is derived through topic_id, so the historical duplicate owner_id
-- column and its constraint are removed to retain the normalized 3NF shape.
SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.table_constraints
     WHERE table_schema = DATABASE() AND table_name = 'note_access_requests'
       AND constraint_name = 'fk_note_access_owner') = 1,
    'ALTER TABLE note_access_requests DROP FOREIGN KEY fk_note_access_owner',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.statistics
     WHERE table_schema = DATABASE() AND table_name = 'note_access_requests'
       AND index_name = 'ix_note_access_owner_id') > 0,
    'ALTER TABLE note_access_requests DROP INDEX ix_note_access_owner_id',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = 'note_access_requests'
       AND column_name = 'owner_id') = 1,
    'ALTER TABLE note_access_requests DROP COLUMN owner_id',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
