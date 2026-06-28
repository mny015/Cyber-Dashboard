from types import SimpleNamespace


class Topic:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.title = kwargs.get("title", "")
        self.slug = kwargs.get("slug", "")
        self.description = kwargs.get("description", "")
        self.status = kwargs.get("status", "planned")
        self.priority = kwargs.get("priority", "medium")
        self.notes = kwargs.get("notes", "")
        self.is_deleted = bool(kwargs.get("is_deleted", False))
        self.category_id = kwargs.get("category_id")
        self.category_name = kwargs.get("category_name")
        self.owner_id = kwargs.get("owner_id")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")

    @property
    def category(self):
        if not self.category_id:
            return None
        return SimpleNamespace(id=self.category_id, name=self.category_name)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)
