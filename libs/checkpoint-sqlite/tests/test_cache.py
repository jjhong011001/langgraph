from contextlib import closing
from pathlib import Path

import pytest

from langgraph.cache.sqlite import SqliteCache


@pytest.mark.parametrize("ttl", [None, 3600])
def test_expired_read_does_not_delete_concurrent_refresh(
    tmp_path: Path, ttl: int | None
):
    path = str(tmp_path / "cache.sqlite")
    reader = SqliteCache(path=path)
    writer = SqliteCache(path=path)
    key = (("retrieval",), "query")
    with closing(reader._conn), closing(writer._conn):
        writer.set({key: ("expired", -1)})
        committed = []

        def before_delete(sql: str) -> None:
            if sql.startswith("DELETE FROM cache"):
                writer.set({key: ("fresh", ttl)})
                committed.append(writer.get([key])[key])

        reader._conn.set_trace_callback(before_delete)
        try:
            assert reader.get([key]) == {}
        finally:
            reader._conn.set_trace_callback(None)

        assert committed == ["fresh"]
        assert writer.get([key]) == {key: "fresh"}

        writer.set({key: ("expired", -1)})
        assert reader.get([key]) == {}
        assert writer._conn.execute("SELECT count(*) FROM cache").fetchone() == (0,)
