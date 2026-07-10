-- Freeze deliberate deletion behavior for every application foreign key.
-- Existing constraint names vary across legacy databases, so each relationship
-- is located through information_schema before the normalized constraint is added.

-- users.profile_image -> profile_images.image_hash: referenced images cannot be
-- removed while an account still uses them.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'profile_image' AND referenced_table_name = 'profile_images' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE users DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE users ADD CONSTRAINT fk_users_profile_image FOREIGN KEY (profile_image) REFERENCES profile_images(image_hash) ON DELETE RESTRICT;

-- User-owned categories have no independent owner after account deletion.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'categories' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE categories DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE categories ADD CONSTRAINT fk_categories_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Private contacts have no meaning without their owner.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'contacts' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE contacts DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE contacts ADD CONSTRAINT fk_contacts_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- A topic survives category deletion because category assignment is optional.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'topics' AND column_name = 'category_id' AND referenced_table_name = 'categories' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE topics DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE topics ADD CONSTRAINT fk_topics_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

-- User-owned topics are private account data.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'topics' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE topics DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE topics ADD CONSTRAINT fk_topics_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Audit evidence must survive account deletion while dropping the actor link.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'user_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE audit_logs DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Private notes are deleted with their owner.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'notes' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE notes DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE notes ADD CONSTRAINT fk_notes_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Notes remain useful when an optional topic is deleted.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'notes' AND column_name = 'topic_id' AND referenced_table_name = 'topics' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE notes DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE notes ADD CONSTRAINT fk_notes_topic FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL;

-- Keep request history if the requesting administrator is deleted.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'requester_admin_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE note_access_requests DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE note_access_requests MODIFY requester_admin_id INT NULL;
ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_admin FOREIGN KEY (requester_admin_id) REFERENCES users(id) ON DELETE SET NULL;

-- A request has no purpose after its requested topic is removed.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'topic_id' AND referenced_table_name = 'topics' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE note_access_requests DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_topic FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;

-- Approved access to one note ends when that note is removed.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'note_id' AND referenced_table_name = 'notes' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE note_access_requests DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_note FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE;

-- Lab references are ownership-controlled; orphaning them would bypass access rules.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE lab_references DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- A lab can remain useful without its optional topic association.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'topic_id' AND referenced_table_name = 'topics' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE lab_references DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_topic FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL;

-- Platform rows are shared reference data and cannot be removed while in use.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'platform_id' AND referenced_table_name = 'lab_platforms' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE lab_references DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_platform FOREIGN KEY (platform_id) REFERENCES lab_platforms(id) ON DELETE RESTRICT;

-- Completion rows have no meaning after their lab is deleted.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND column_name = 'lab_id' AND referenced_table_name = 'lab_references' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE lab_completions DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE lab_completions ADD CONSTRAINT fk_lab_completions_lab FOREIGN KEY (lab_id) REFERENCES lab_references(id) ON DELETE CASCADE;

-- A user's completion records are private user activity.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND column_name = 'user_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE lab_completions DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE lab_completions ADD CONSTRAINT fk_lab_completions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Catalog suggestions survive after their creator account is removed.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND column_name = 'created_by_user_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE vulnerability_catalog DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE vulnerability_catalog ADD CONSTRAINT fk_vulnerability_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Review outcomes survive after the reviewing administrator is removed.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND column_name = 'reviewed_by_user_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE vulnerability_catalog DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE vulnerability_catalog ADD CONSTRAINT fk_vulnerability_reviewed_by FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Findings are private user-owned records.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE security_findings DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Finding evidence survives catalog cleanup without the optional classification.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'vulnerability_id' AND referenced_table_name = 'vulnerability_catalog' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE security_findings DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability_catalog(id) ON DELETE SET NULL;

-- Threat classification is optional historical metadata on a finding.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'threat_id' AND referenced_table_name = 'threat_catalog' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE security_findings DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_threat FOREIGN KEY (threat_id) REFERENCES threat_catalog(id) ON DELETE SET NULL;

-- A user-specific task has no purpose after its assignee is deleted. Shared
-- tasks have a NULL user_id and are unaffected by this cascade.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND column_name = 'user_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE scheduled_tasks DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE scheduled_tasks ADD CONSTRAINT fk_scheduled_tasks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Shared task history survives creator deletion.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND column_name = 'created_by' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE scheduled_tasks DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE scheduled_tasks MODIFY created_by INT NULL;
ALTER TABLE scheduled_tasks ADD CONSTRAINT fk_scheduled_tasks_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Historical work logs are private user-owned records.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'work_logs' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE work_logs DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE work_logs ADD CONSTRAINT fk_work_logs_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Roadmap items remain useful if their optional topic is removed.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND column_name = 'topic_id' AND referenced_table_name = 'topics' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE roadmap_items DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE roadmap_items ADD CONSTRAINT fk_roadmap_items_topic FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL;

-- Roadmap items are private user-owned planning data.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE roadmap_items DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE roadmap_items ADD CONSTRAINT fk_roadmap_items_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Reflections are private user-owned records.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'progress_reflections' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE progress_reflections DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE progress_reflections ADD CONSTRAINT fk_progress_reflections_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Aggregate activity history survives account deletion without identifying the user.
SET @fk_name = (SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'activity_events' AND column_name = 'owner_id' AND referenced_table_name = 'users' LIMIT 1);
SET @migration_sql = IF(@fk_name IS NULL, 'SELECT 1', CONCAT('ALTER TABLE activity_events DROP FOREIGN KEY `', @fk_name, '`'));
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
ALTER TABLE activity_events MODIFY owner_id INT NULL;
ALTER TABLE activity_events ADD CONSTRAINT fk_activity_events_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL;
