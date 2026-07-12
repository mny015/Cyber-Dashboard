from app.models import Note
from app.repositories import note_repository, topic_repository
from app.utils.database.query_builder import Database, WriteResult


class RecordingDatabase(Database):
    def __init__(self):
        self.calls = []
        self.one_result = None

    def _fetch_one(self, sql, params):
        self.calls.append(("one", sql, params))
        return self.one_result

    def _execute(self, sql, params):
        self.calls.append(("execute", sql, params))
        return WriteResult(1, 12)


def test_note_update_repeats_ownership_in_write_query(monkeypatch):
    database = RecordingDatabase()
    monkeypatch.setattr(note_repository, "db", database)
    note = Note(id=6, title="Updated", body="Body", owner_id=11)

    note_repository.update_owned(note, 11)

    _kind, sql, params = database.calls[0]
    assert sql.startswith("UPDATE `notes` SET")
    assert "WHERE `id` = %s AND `owner_id` = %s AND `is_deleted` = %s" in sql
    assert params[-3:] == (6, 11, False)


def test_topic_permission_check_is_owner_scoped(monkeypatch):
    database = RecordingDatabase()
    database.one_result = {"exists_value": 1}
    monkeypatch.setattr(topic_repository, "db", database)

    assert topic_repository.exists_owned(5, 9) is True

    _kind, sql, params = database.calls[0]
    assert "`id` = %s AND `owner_id` = %s AND `is_deleted` = %s" in sql
    assert params == (5, 9, False, 1)
