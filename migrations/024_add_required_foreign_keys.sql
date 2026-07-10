-- Restore relationships missing from historical databases. Guards compare the
-- relationship itself, so an equivalent legacy constraint is not duplicated.

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'profile_image' AND referenced_table_name = 'profile_images' AND referenced_column_name = 'image_hash') = 0, 'ALTER TABLE users ADD CONSTRAINT fk_users_profile_image FOREIGN KEY (profile_image) REFERENCES profile_images(image_hash)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'categories' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE categories ADD CONSTRAINT fk_categories_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'contacts' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE contacts ADD CONSTRAINT fk_contacts_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'topics' AND column_name = 'category_id' AND referenced_table_name = 'categories' AND referenced_column_name = 'id') = 0, 'ALTER TABLE topics ADD CONSTRAINT fk_topics_category FOREIGN KEY (category_id) REFERENCES categories(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'topics' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE topics ADD CONSTRAINT fk_topics_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'user_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'notes' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE notes ADD CONSTRAINT fk_notes_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'notes' AND column_name = 'topic_id' AND referenced_table_name = 'topics' AND referenced_column_name = 'id') = 0, 'ALTER TABLE notes ADD CONSTRAINT fk_notes_topic FOREIGN KEY (topic_id) REFERENCES topics(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'requester_admin_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_admin FOREIGN KEY (requester_admin_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'topic_id' AND referenced_table_name = 'topics' AND referenced_column_name = 'id') = 0, 'ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_topic FOREIGN KEY (topic_id) REFERENCES topics(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'note_access_requests' AND column_name = 'note_id' AND referenced_table_name = 'notes' AND referenced_column_name = 'id') = 0, 'ALTER TABLE note_access_requests ADD CONSTRAINT fk_note_access_note FOREIGN KEY (note_id) REFERENCES notes(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'topic_id' AND referenced_table_name = 'topics' AND referenced_column_name = 'id') = 0, 'ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_topic FOREIGN KEY (topic_id) REFERENCES topics(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_references' AND column_name = 'platform_id' AND referenced_table_name = 'lab_platforms' AND referenced_column_name = 'id') = 0, 'ALTER TABLE lab_references ADD CONSTRAINT fk_lab_references_platform FOREIGN KEY (platform_id) REFERENCES lab_platforms(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND column_name = 'lab_id' AND referenced_table_name = 'lab_references' AND referenced_column_name = 'id') = 0, 'ALTER TABLE lab_completions ADD CONSTRAINT fk_lab_completions_lab FOREIGN KEY (lab_id) REFERENCES lab_references(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'lab_completions' AND column_name = 'user_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE lab_completions ADD CONSTRAINT fk_lab_completions_user FOREIGN KEY (user_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND column_name = 'created_by_user_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE vulnerability_catalog ADD CONSTRAINT fk_vulnerability_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'vulnerability_catalog' AND column_name = 'reviewed_by_user_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE vulnerability_catalog ADD CONSTRAINT fk_vulnerability_reviewed_by FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'vulnerability_id' AND referenced_table_name = 'vulnerability_catalog' AND referenced_column_name = 'id') = 0, 'ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability_catalog(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'security_findings' AND column_name = 'threat_id' AND referenced_table_name = 'threat_catalog' AND referenced_column_name = 'id') = 0, 'ALTER TABLE security_findings ADD CONSTRAINT fk_security_findings_threat FOREIGN KEY (threat_id) REFERENCES threat_catalog(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND column_name = 'user_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE scheduled_tasks ADD CONSTRAINT fk_scheduled_tasks_user FOREIGN KEY (user_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'scheduled_tasks' AND column_name = 'created_by' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE scheduled_tasks ADD CONSTRAINT fk_scheduled_tasks_created_by FOREIGN KEY (created_by) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'work_logs' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE work_logs ADD CONSTRAINT fk_work_logs_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND column_name = 'topic_id' AND referenced_table_name = 'topics' AND referenced_column_name = 'id') = 0, 'ALTER TABLE roadmap_items ADD CONSTRAINT fk_roadmap_items_topic FOREIGN KEY (topic_id) REFERENCES topics(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'roadmap_items' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE roadmap_items ADD CONSTRAINT fk_roadmap_items_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'progress_reflections' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE progress_reflections ADD CONSTRAINT fk_progress_reflections_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @migration_sql = IF((SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name = 'activity_events' AND column_name = 'owner_id' AND referenced_table_name = 'users' AND referenced_column_name = 'id') = 0, 'ALTER TABLE activity_events ADD CONSTRAINT fk_activity_events_owner FOREIGN KEY (owner_id) REFERENCES users(id)', 'SELECT 1');
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
