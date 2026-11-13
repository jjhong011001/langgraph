from typing import Any

from langgraph.cache.memory import InMemoryCache

from langgraph.func import entrypoint, task
from langgraph.types import CachePolicy


def test_default_cache_key_distinguishes_mapping_and_sequence() -> None:
    calls = []

    @task(cache_policy=CachePolicy())
    def lookup(*, query: Any) -> str:
        calls.append(query)
        return "mapping" if isinstance(query, dict) else "sequence"

    @entrypoint(cache=InMemoryCache())
    def graph(query: Any) -> str:
        return lookup(query=query).result()

    for query, expected in [
        ({}, "mapping"),
        ([], "sequence"),
        ({"a": 1, "b": 2}, "mapping"),
        ({"b": 2, "a": 1}, "mapping"),
        ({}, "mapping"),
        ([], "sequence"),
    ]:
        assert graph.invoke(query) == expected
    assert calls == [{}, [], {"a": 1, "b": 2}]
