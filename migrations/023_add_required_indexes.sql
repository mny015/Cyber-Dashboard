-- Restore every named unique and lookup index expected by the application.
-- Missing unique indexes intentionally fail when legacy duplicate data exists;
-- the runner never deletes or rewrites user data to force uniqueness.

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'users' AND index_name = 'uq_users_email') = 0, 'ALTER TABLE users ADD UNIQUE INDEX uq_users_email (email)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'categories' AND index_name = 'uq_category_owner_name') = 0, 'ALTER TABLE categories ADD UNIQUE INDEX uq_category_owner_name (owner_id, name)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'categories' AND index_name = 'ix_categories_owner_id') = 0, 'ALTER TABLE categories ADD INDEX ix_categories_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'contacts' AND index_name = 'ix_contacts_owner_id') = 0, 'ALTER TABLE contacts ADD INDEX ix_contacts_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'topics' AND index_name = 'uq_topic_owner_slug') = 0, 'ALTER TABLE topics ADD UNIQUE INDEX uq_topic_owner_slug (owner_id, slug)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'topics' AND index_name = 'ix_topics_owner_id') = 0, 'ALTER TABLE topics ADD INDEX ix_topics_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND index_name = 'ix_audit_logs_user_id') = 0, 'ALTER TABLE audit_logs ADD INDEX ix_audit_logs_user_id (user_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'notes' AND index_name = 'ix_notes_owner_id') = 0, 'ALTER TABLE notes ADD INDEX ix_notes_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'notes' AND index_name = 'ix_notes_topic_id') = 0, 'ALTER TABLE notes ADD INDEX ix_notes_topic_id (topic_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND index_name = 'ix_note_access_admin_id') = 0, 'ALTER TABLE note_access_requests ADD INDEX ix_note_access_admin_id (requester_admin_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND index_name = 'ix_note_access_topic_id') = 0, 'ALTER TABLE note_access_requests ADD INDEX ix_note_access_topic_id (topic_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND index_name = 'ix_note_access_note_id') = 0, 'ALTER TABLE note_access_requests ADD INDEX ix_note_access_note_id (note_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_platforms' AND index_name = 'uq_lab_platform_name') = 0, 'ALTER TABLE lab_platforms ADD UNIQUE INDEX uq_lab_platform_name (name)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_platforms' AND index_name = 'uq_lab_platform_slug') = 0, 'ALTER TABLE lab_platforms ADD UNIQUE INDEX uq_lab_platform_slug (slug)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_owner_id') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_topic_id') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_topic_id (topic_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND index_name = 'ix_lab_references_platform_id') = 0, 'ALTER TABLE lab_references ADD INDEX ix_lab_references_platform_id (platform_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND index_name = 'uq_lab_completion_user') = 0, 'ALTER TABLE lab_completions ADD UNIQUE INDEX uq_lab_completion_user (lab_id, user_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND index_name = 'ix_lab_completions_user_id') = 0, 'ALTER TABLE lab_completions ADD INDEX ix_lab_completions_user_id (user_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND index_name = 'uq_vulnerability_code') = 0, 'ALTER TABLE vulnerability_catalog ADD UNIQUE INDEX uq_vulnerability_code (code)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND index_name = 'ix_vulnerability_status') = 0, 'ALTER TABLE vulnerability_catalog ADD INDEX ix_vulnerability_status (approval_status)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'threat_catalog' AND index_name = 'uq_threat_code') = 0, 'ALTER TABLE threat_catalog ADD UNIQUE INDEX uq_threat_code (code)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND index_name = 'ix_security_findings_owner_id') = 0, 'ALTER TABLE security_findings ADD INDEX ix_security_findings_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND index_name = 'ix_security_findings_vulnerability_id') = 0, 'ALTER TABLE security_findings ADD INDEX ix_security_findings_vulnerability_id (vulnerability_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND index_name = 'ix_security_findings_threat_id') = 0, 'ALTER TABLE security_findings ADD INDEX ix_security_findings_threat_id (threat_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_tasks_user_id') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_tasks_user_id (user_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_tasks_created_by') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_tasks_created_by (created_by)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND index_name = 'ix_scheduled_tasks_scope_status') = 0, 'ALTER TABLE scheduled_tasks ADD INDEX ix_scheduled_tasks_scope_status (scope, status)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'work_logs' AND index_name = 'ix_work_logs_owner_id') = 0, 'ALTER TABLE work_logs ADD INDEX ix_work_logs_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND index_name = 'ix_roadmap_items_owner_id') = 0, 'ALTER TABLE roadmap_items ADD INDEX ix_roadmap_items_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND index_name = 'ix_roadmap_items_topic_id') = 0, 'ALTER TABLE roadmap_items ADD INDEX ix_roadmap_items_topic_id (topic_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'progress_reflections' AND index_name = 'ix_progress_reflections_owner_id') = 0, 'ALTER TABLE progress_reflections ADD INDEX ix_progress_reflections_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'activity_events' AND index_name = 'ix_activity_events_owner_id') = 0, 'ALTER TABLE activity_events ADD INDEX ix_activity_events_owner_id (owner_id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
