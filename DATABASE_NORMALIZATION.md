# Database Normalization

The Cyber Dashboard MySQL schema has been reviewed and normalized through Third Normal Form (3NF).

## First Normal Form (1NF)

- Every table has a primary key.
- Columns contain atomic values rather than repeating groups or comma-separated lists.
- Many-to-many and per-user state are stored separately, such as `lab_completions`.

## Second Normal Form (2NF)

- Non-key columns depend on the whole candidate key.
- Junction state such as lab completion depends on the unique pair `(lab_id, user_id)`.
- Tables using surrogate primary keys also enforce natural uniqueness where required, including user email and category name per owner.

## Third Normal Form (3NF)

The following transitive or redundant dependencies were removed:

### Profile images

Before:

`user_id -> profile_image_hash -> image_data, MIME type, byte size`

The image data and metadata were stored in `users`, even though they depend on the image hash.

After:

- `users.profile_image` stores only the image hash.
- `profile_images.image_hash` is the primary key.
- Image bytes, MIME type, and byte size are stored once in `profile_images`.

### Lab platforms

Before:

Platform/vendor names were repeated in every `lab_references` row.

After:

- Platform names and slugs are stored in `lab_platforms`.
- `lab_references.platform_id` references `lab_platforms.id`.
- Repeated platform text is no longer stored with every lab.

### Note access requests

Before:

`request_id -> topic_id -> owner_id`

`owner_id` was duplicated in `note_access_requests`, even though the topic already determines its owner.

After:

- `note_access_requests` stores `topic_id`.
- The owner is obtained through `topics.owner_id`.
- The redundant `owner_id` column was removed.

## Tables Already Meeting 3NF

The following structures already had atomic attributes with non-key values depending directly on their keys:

- `users`
- `categories`
- `topics`
- `notes`
- `contacts`
- `lab_completions`
- `audit_logs`
- `activity_events`
- `progress_reflections`
- `roadmap_items`
- `work_logs`

Status, priority, visibility, and role values remain constrained domain attributes. Separate lookup tables are not required for 3NF unless additional metadata or configurable values are introduced.
