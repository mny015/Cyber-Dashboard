# Controller Map

All 71 application routes map directly to these plain controller functions. Route modules contain only Blueprint setup and `add_url_rule()` declarations. Authentication and administrator decorators are applied to the controller functions.

## Dashboard Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | None | `index.html` |
| `dashboard` | `current_user` | Redirects to `dashboard.admin_dashboard` or `dashboard.user_dashboard` |
| `user_dashboard` | `dashboard_service.user_dashboard_data` | `user/dashboard.html`, or redirects administrators |
| `admin_dashboard` | `dashboard_service.admin_dashboard_data` | `admin/dashboard.html` |

## Authentication Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `register` | `RegisterForm`, `auth_service.register` | `auth/register.html` or `auth.login` |
| `login` | `LoginForm`, `auth_service.authenticate` | `auth/login.html`, `auth.verify_mfa`, or a role dashboard |
| `verify_mfa` | `MfaTokenForm`, `user_repository.find_by_id`, `auth_service.verify_mfa_token` | `auth/verify_mfa.html`, `auth.login`, or a role dashboard |
| `logout` | `log_audit`, Flask-Login/session cleanup | `auth.login` |
| `setup_mfa` | `MfaSetupForm`, `ChangePasswordForm`, MFA service functions | `auth/setup_mfa.html` or `dashboard.dashboard` |
| `mfa_qr` | `pyotp`, `qrcode` | PNG response, `auth.setup_mfa`, or 404 |
| `change_password` | `ChangePasswordForm`, `auth_service.change_password` | `auth.setup_mfa` or `auth.login` |

## Administrator Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `users` | `user_repository.list_all` | `admin/users.html` |
| `topic_summaries` | `topic_repository.list_admin_summaries` | `admin/topic_summaries.html` |
| `request_topic_notes` | `notification_service.request_note_access` | `admin.note_requests`, `admin.topic_summaries`, or 404 |
| `note_requests` | `notification_repository.list_for_admin` | `admin/note_requests.html` |
| `approved_note` | `notification_repository.find_approved_note` | `admin/approved_note.html` or 404 |
| `category_summaries` | `category_repository.list_admin_summaries` | `admin/category_summaries.html` |
| `update_role` | `RoleForm`, `user_repository.find_by_id`, `user_management_service.change_role` | `admin.users` |
| `ban_user` | `_set_banned`, user-management service | `admin.users` |
| `unban_user` | `_set_banned`, user-management service | `admin.users` |
| `reset_user_password` | `AdminPasswordResetForm`, user repository/service | `admin.users` |
| `delete_user` | `user_repository.find_by_id`, `user_management_service.delete_user` | `admin.users` |
| `audit_logs` | `audit_repository.paginate` | `admin/audit_logs.html` |

## Backup Controller

| Function | Calls | Template or response |
|---|---|---|
| `index` | None | `backup/index.html` |
| `personal_json` | `ActionForm`, export audit, ticket creation | Redirects to `backup.download` |
| `personal_csv` | `ActionForm`, export audit, ticket creation | Redirects to `backup.download` |
| `admin_json` | `ActionForm`, export audit, ticket creation | Redirects to `backup.download` |
| `admin_csv` | `ActionForm`, export audit, ticket creation | Redirects to `backup.download` |
| `download` | Short-lived ticket validation, export service | JSON or ZIP download |

## API Controller

| Function | Calls | Response |
|---|---|---|
| `ping` | `jsonify` | API status JSON |

## Category Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | `category_repository.list_for_user` | `categories/index.html` |
| `create` | `category_repository.create`, `log_audit` | `categories/form.html` or `categories.index` |
| `edit` | Category repository, `log_audit` | `categories/form.html`, `categories.index`, or 404 |
| `delete` | `category_repository.delete_owned`, `log_audit` | `categories.index` or 404 |

## Contact Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | `contact_repository.list_for_user` | `contacts/index.html` |
| `create` | Contact validation, `contact_repository.create`, `log_audit` | `contacts/form.html` or `contacts.index` |
| `edit` | Contact validation/repository, `log_audit` | `contacts/form.html`, `contacts.index`, or 404 |
| `delete` | `contact_repository.delete_owned`, `log_audit` | `contacts.index` or 404 |

## Topic Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | Topic/category repositories | `topics/index.html` |
| `create` | Topic validation/repository, `log_audit` | `topics/form.html` or `topics.detail` |
| `detail` | `topic_repository.find_owned` | `topics/detail.html` or 404 |
| `edit` | Topic validation/repository, `log_audit` | `topics/form.html`, `topics.detail`, or 404 |
| `delete` | `topic_repository.delete_owned`, `log_audit` | `topics.index` or 404 |

## Note Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | Note/topic repositories | `notes/index.html` or 404 |
| `create` | `note_service.create_note` | `notes/form.html`, `notes.detail`, or 403 |
| `detail` | `note_repository.find_owned` | `notes/detail.html` or 404 |
| `edit` | Note repository/service | `notes/form.html`, `notes.detail`, 403, or 404 |
| `delete` | `note_service.delete_note` | `notes.index` or 404 |

## Lab Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | `lab_repository.list_visible`, platform repository read | `labs/index.html` |
| `create` | Lab/topic validation, `lab_repository.create`, `log_audit` | `labs/form.html` or `labs.detail` |
| `detail` | `lab_repository.find_visible` | `labs/detail.html` or 404 |
| `edit` | Lab/topic validation, `lab_repository.update_owned`, `log_audit` | `labs/form.html`, `labs.detail`, or 404 |
| `delete` | `lab_repository.delete_owned`, `log_audit` | `labs.index` or 404 |
| `complete` | `lab_repository.mark_completed_if_visible`, `log_audit` | `labs.detail` or 404 |
| `incomplete` | `lab_repository.mark_incomplete` | `labs.detail` or 404 |

## Notification Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | Notification repository reads | `notifications/index.html` |
| `approve` | `notification_service.approve_request` | `notifications.index` or 404 |
| `deny` | `notification_service.deny_request` | `notifications.index` or 404 |

## Profile Controller

| Function | Calls | Template or response |
|---|---|---|
| `edit` | `ProfileForm`, user repository, `profile_images`, `log_audit` | `profile/edit.html` or `profile.edit` |
| `picture` | `user_repository.find_owned_profile_image` | Private image response or 404 |

## Security Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | Security repository reads | `security/index.html` |
| `create` | Security repository/service | `security/form.html` or `security.index` |
| `edit` | Security repository/service | `security/form.html`, `security.index`, 403, or 404 |
| `delete` | `security_service.delete_finding` | `security.index` or 404 |
| `suggest_vulnerability` | `security_service.suggest_vulnerability` | `security.index` |
| `admin_vulnerabilities` | Security repository/service | `security/admin_vulnerabilities.html` or same endpoint redirect |
| `approve_vulnerability` | `security_service.review_vulnerability` | `security.admin_vulnerabilities` |
| `reject_vulnerability` | `security_service.review_vulnerability` | `security.admin_vulnerabilities` |

## Scheduled Task Controller

| Function | Calls | Template or redirect |
|---|---|---|
| `index` | Scheduled-task repository/service | `tasks/index.html` or `tasks.index` |
| `complete` | `scheduled_task_service.set_status` | `tasks.index`, 403, or 404 |
| `cancel` | `scheduled_task_service.set_status` | `tasks.index`, 403, or 404 |

## Private Controller Helpers

| Controller | Helpers | Purpose |
|---|---|---|
| Admin | `_set_banned` | Shared ban/unban response handling |
| Authentication | `_complete_login` | Session creation, audit, and role redirect |
| Categories | `_get_category_or_404` | Ownership-scoped lookup |
| Contacts | `_get_contact_or_404`, `_apply_form`, `_is_valid` | Ownership, request mapping, validation |
| Dashboard | `_default_admin_tasks` | HTTP URLs for fallback admin actions |
| Labs | `_visible_lab_or_404`, `_owned_lab_or_404`, `_render_form`, `_read_form`, `_validation_error`, `_lab_model` | Visibility, form mapping, validation |
| Notes | `_get_note_or_404`, `_topics` | Ownership lookup and form choices |
| Notifications | `_get_pending_request_or_404` | Ownership-scoped pending request lookup |
| Scheduled tasks | `_visible_tasks`, `_read_form`, `_change_status`, `_parse_due_at` | Form mapping and exception translation |
| Security | `_save_finding`, `_finding_or_404`, `_render_finding_form`, `_review_vulnerability` | Form handling and domain exception translation |
| Topics | `_get_topic_or_404`, `_categories`, `_apply_form`, `_save` | Ownership, form mapping, duplicate handling |
