-- Retire the obsolete Alembic ledger after numbered SQL history is recorded.
-- It contains migration metadata only; application data remains untouched.
SET @migration_sql = IF(
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema = DATABASE() AND table_name = 'alembic_version') = 1,
    'DROP TABLE alembic_version',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
