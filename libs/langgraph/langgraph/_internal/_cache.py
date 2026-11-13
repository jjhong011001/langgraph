from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from typing import Any


def _normalize(obj: Any, depth: int = 10) -> Any:
    if depth <= 0:
        return obj
    if isinstance(obj, tuple):
        return tuple(_normalize(item, depth - 1) for item in obj)
    if isinstance(obj, Hashable):
        return obj
    if isinstance(obj, Mapping):
        return {key: _normalize(obj[key], depth - 1) for key in sorted(obj)}
    if isinstance(obj, Sequence):
        return [_normalize(item, depth - 1) for item in obj]
    # numpy / pandas etc. can provide their own .tobytes()
    elif hasattr(obj, "tobytes"):
        return (
            type(obj).__name__,
            obj.tobytes(),
            obj.shape if hasattr(obj, "shape") else None,
        )
    return obj  # strings, ints, dataclasses with frozen=True, etc.


def default_cache_key(*args: Any, **kwargs: Any) -> str | bytes:
    """Default cache key function that uses the arguments and keyword arguments to generate a hashable key."""
    import pickle

    # protocol 5 strikes a good balance between speed and size
    normalized_kwargs = tuple(
        (key, _normalize(value)) for key, value in sorted(kwargs.items())
    )
    return pickle.dumps(
        (_normalize(args), normalized_kwargs), protocol=5, fix_imports=False
    )
