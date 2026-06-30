class Contact:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name", "")
        self.email = kwargs.get("email", "")
        self.phone = kwargs.get("phone", "")
        self.notes = kwargs.get("notes", "")
        self.is_deleted = bool(kwargs.get("is_deleted", False))
        self.owner_id = kwargs.get("owner_id")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)
