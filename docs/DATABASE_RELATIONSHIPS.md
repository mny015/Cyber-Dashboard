# Database Relationship Policy

Migration `026_freeze_foreign_key_delete_rules.sql` freezes the deletion policy
for every application foreign key. `027_add_relationship_query_indexes.sql`
adds composite indexes for common ownership, status, join, and ordering paths.

## Foreign Keys

| Child column | Parent column | Delete rule | Decision |
|---|---|---|---|
| `users.profile_image` | `profile_images.image_hash` | RESTRICT | An image cannot be removed while an account references it. |
| `categories.owner_id` | `users.id` | CASCADE | A private category has no owner-independent purpose. |
| `contacts.owner_id` | `users.id` | CASCADE | A private contact has no owner-independent purpose. |
| `topics.category_id` | `categories.id` | SET NULL | Category assignment is optional; the topic remains useful. |
| `topics.owner_id` | `users.id` | CASCADE | A private topic belongs to one account. |
| `audit_logs.user_id` | `users.id` | SET NULL | Audit evidence must survive account deletion. |
| `notes.owner_id` | `users.id` | CASCADE | A private note belongs to one account. |
| `notes.topic_id` | `topics.id` | SET NULL | A note remains useful without its optional topic. |
| `note_access_requests.requester_admin_id` | `users.id` | SET NULL | Request history survives administrator deletion. |
| `note_access_requests.topic_id` | `topics.id` | CASCADE | A request has no purpose without its requested topic. |
| `note_access_requests.note_id` | `notes.id` | CASCADE | Approval for one note ends when that note is removed. |
| `lab_references.owner_id` | `users.id` | CASCADE | Ownership drives lab privacy and edit authorization. |
| `lab_references.topic_id` | `topics.id` | SET NULL | A lab remains useful without an optional topic. |
| `lab_references.platform_id` | `lab_platforms.id` | RESTRICT | Shared platform reference data cannot be removed while used. |
| `lab_completions.lab_id` | `lab_references.id` | CASCADE | A completion has no meaning without its lab. |
| `lab_completions.user_id` | `users.id` | CASCADE | Completion history is private account data. |
| `vulnerability_catalog.created_by_user_id` | `users.id` | SET NULL | Catalog suggestions survive creator deletion. |
| `vulnerability_catalog.reviewed_by_user_id` | `users.id` | SET NULL | Review outcomes survive administrator deletion. |
| `security_findings.owner_id` | `users.id` | CASCADE | A finding is private user-owned data. |
| `security_findings.vulnerability_id` | `vulnerability_catalog.id` | SET NULL | Finding evidence survives catalog cleanup. |
| `security_findings.threat_id` | `threat_catalog.id` | SET NULL | Threat classification is optional historical metadata. |
| `scheduled_tasks.user_id` | `users.id` | CASCADE | An assigned task has no purpose after its assignee is removed. |
| `scheduled_tasks.created_by` | `users.id` | SET NULL | Shared task history survives creator deletion. |
| `work_logs.owner_id` | `users.id` | CASCADE | A work log is private user-owned data. |
| `roadmap_items.topic_id` | `topics.id` | SET NULL | A roadmap item survives optional topic deletion. |
| `roadmap_items.owner_id` | `users.id` | CASCADE | A roadmap item is private user-owned data. |
| `progress_reflections.owner_id` | `users.id` | CASCADE | A reflection is private user-owned data. |
| `activity_events.owner_id` | `users.id` | SET NULL | Aggregate historical activity survives without user identity. |

The current schema has no separate `notifications`, MFA recovery-code, or
user-settings tables. Note-access requests provide the current notification
workflow. Any future table must receive an explicit policy before its migration
is accepted.

## Index Policy

Every foreign-key column has a supporting index. Composite indexes additionally
cover the main query shapes:

- Owner plus soft-delete and update/detection timestamps for topics, notes,
  categories, labs, and findings.
- Status plus due/request timestamps for scheduled tasks and note requests.
- Visibility, platform, and completion paths for lab dashboards.
- Actor plus timestamp for audit history.
- Catalog approval/active filters and creator review queues.
- Historical owner/date paths for work logs, roadmap items, reflections, and
  activity events.

This relationship design is frozen. Change it only through a new numbered
migration that fixes a demonstrated defect and updates the relationship contract.
