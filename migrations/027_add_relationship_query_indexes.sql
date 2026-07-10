-- Composite indexes for frequent ownership filters, status filters, joins, and
-- dashboard/list ordering. Single-column foreign-key indexes already exist.

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'users' AND index_name = 'ix_users_role_banned') = 0, 'ALTER TABLE users ADD INDEX ix_users_role_banned (role, is_banned)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'users' AND index_name = 'ix_users_created_at') = 0, 'ALTER TABLE users ADD INDEX ix_users_created_at (created_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND index_name = 'ix_audit_logs_created_at') = 0, 'ALTER TABLE audit_logs ADD INDEX ix_audit_logs_created_at (created_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND index_name = 'ix_audit_logs_user_created') = 0, 'ALTER TABLE audit_logs ADD INDEX ix_audit_logs_user_created (user_id, created_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'categories' AND index_name = 'ix_categories_owner_deleted_name') = 0, 'ALTER TABLE categories ADD INDEX ix_categories_owner_deleted_name (owner_id, is_deleted, name)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'categories' AND index_name = 'ix_categories_deleted_updated') = 0, 'ALTER TABLE categories ADD INDEX ix_categories_deleted_updated (is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'topics' AND index_name = 'ix_topics_owner_deleted_updated') = 0, 'ALTER TABLE topics ADD INDEX ix_topics_owner_deleted_updated (owner_id, is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'topics' AND index_name = 'ix_topics_category_deleted') = 0, 'ALTER TABLE topics ADD INDEX ix_topics_category_deleted (category_id, is_deleted)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'topics' AND index_name = 'ix_topics_deleted_updated') = 0, 'ALTER TABLE topics ADD INDEX ix_topics_deleted_updated (is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'notes' AND index_name = 'ix_notes_owner_deleted_updated') = 0, 'ALTER TABLE notes ADD INDEX ix_notes_owner_deleted_updated (owner_id, is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'notes' AND index_name = 'ix_notes_topic_owner_deleted') = 0, 'ALTER TABLE notes ADD INDEX ix_notes_topic_owner_deleted (topic_id, owner_id, is_deleted)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'notes' AND index_name = 'ix_notes_deleted_updated') = 0, 'ALTER TABLE notes ADD INDEX ix_notes_deleted_updated (is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND index_name = 'ix_note_access_status_requested') = 0, 'ALTER TABLE note_access_requests ADD INDEX ix_note_access_status_requested (status, requested_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND index_name = 'ix_note_access_topic_status') = 0, 'ALTER TABLE note_access_requests ADD INDEX ix_note_access_topic_status (topic_id, status)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_owner_deleted_updated') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_owner_deleted_updated (owner_id, is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_deleted_visibility_updated') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_deleted_visibility_updated (is_deleted, visibility, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_platform_deleted_updated') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_platform_deleted_updated (platform_id, is_deleted, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND index_name = 'ix_lab_completions_user_completed') = 0, 'ALTER TABLE lab_completions ADD INDEX ix_lab_completions_user_completed (user_id, completed_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND index_name = 'ix_vulnerability_creator_status_created') = 0, 'ALTER TABLE vulnerability_catalog ADD INDEX ix_vulnerability_creator_status_created (created_by_user_id, approval_status, created_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND index_name = 'ix_vulnerability_status_active') = 0, 'ALTER TABLE vulnerability_catalog ADD INDEX ix_vulnerability_status_active (approval_status, is_active)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'threat_catalog' AND index_name = 'ix_threat_active_level_name') = 0, 'ALTER TABLE threat_catalog ADD INDEX ix_threat_active_level_name (is_active, default_level, name)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND index_name = 'ix_security_owner_deleted_detected') = 0, 'ALTER TABLE security_findings ADD INDEX ix_security_owner_deleted_detected (owner_id, is_deleted, detected_at, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_user_status_due') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_user_status_due (user_id, status, due_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_scope_status_due') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_scope_status_due (scope, status, due_at, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_creator_status_updated') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_creator_status_updated (created_by, status, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_status_due_updated') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_status_due_updated (status, due_at, updated_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'work_logs' AND index_name = 'ix_work_logs_owner_date') = 0, 'ALTER TABLE work_logs ADD INDEX ix_work_logs_owner_date (owner_id, log_date)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND index_name = 'ix_roadmap_owner_status_due') = 0, 'ALTER TABLE roadmap_items ADD INDEX ix_roadmap_owner_status_due (owner_id, status, due_date)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'progress_reflections' AND index_name = 'ix_progress_owner_created') = 0, 'ALTER TABLE progress_reflections ADD INDEX ix_progress_owner_created (owner_id, created_at)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'activity_events' AND index_name = 'ix_activity_owner_occurred') = 0, 'ALTER TABLE activity_events ADD INDEX ix_activity_owner_occurred (owner_id, occurred_on)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
