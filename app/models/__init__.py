"""Plain dataclass models and the table-to-model registry."""

from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.contact import Contact
from app.models.lab import LabCompletion, LabPlatform, LabReference
from app.models.learning import ActivityEvent, ProgressReflection, RoadmapItem, WorkLog
from app.models.note import Note
from app.models.note_access_request import NoteAccessRequest, Notification
from app.models.profile_image import ProfileImage
from app.models.scheduled_task import ScheduledTask
from app.models.security import SecurityFinding, ThreatCatalogEntry, VulnerabilityCatalogEntry
from app.models.topic import Topic
from app.models.user import User

MODEL_REGISTRY = {
    model.TABLE_NAME: model
    for model in (
        ProfileImage,
        LabPlatform,
        User,
        VulnerabilityCatalogEntry,
        ThreatCatalogEntry,
        SecurityFinding,
        Category,
        Contact,
        Topic,
        AuditLog,
        Note,
        NoteAccessRequest,
        LabReference,
        LabCompletion,
        ScheduledTask,
        WorkLog,
        RoadmapItem,
        ProgressReflection,
        ActivityEvent,
    )
}


__all__ = [
    "ActivityEvent",
    "AuditLog",
    "Category",
    "Contact",
    "LabCompletion",
    "LabPlatform",
    "LabReference",
    "MODEL_REGISTRY",
    "Note",
    "NoteAccessRequest",
    "Notification",
    "ProfileImage",
    "ProgressReflection",
    "RoadmapItem",
    "ScheduledTask",
    "SecurityFinding",
    "ThreatCatalogEntry",
    "Topic",
    "User",
    "VulnerabilityCatalogEntry",
    "WorkLog",
]
