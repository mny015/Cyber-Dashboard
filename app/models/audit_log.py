from types import SimpleNamespace


class AuditLog:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.action = kwargs.get("action", "")
        self.details = kwargs.get("details", "")
        self.ip_address = kwargs.get("ip_address", "")
        self.user_id = kwargs.get("user_id")
        self.user_email = kwargs.get("user_email")
        self.created_at = kwargs.get("created_at")

    @property
    def user(self):
        if not self.user_email:
            return None
        return SimpleNamespace(email=self.user_email)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)
