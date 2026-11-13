import httpx
import pytest
from langgraph_sdk.client import LangGraphClient, SyncLangGraphClient

from langgraph.pregel.remote import RemoteGraph


@pytest.mark.anyio
@pytest.mark.parametrize("async_mode", [False, True])
async def test_state_request_route_depends_on_checkpoint_selector(async_mode: bool):
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        return httpx.Response(
            200,
            json={
                "values": {},
                "next": [],
                "tasks": [],
                "checkpoint": {
                    "thread_id": "thread",
                    "checkpoint_id": "id",
                    "checkpoint_ns": "",
                },
                "metadata": {},
                "created_at": None,
                "parent_checkpoint": None,
            },
        )

    base = {"configurable": {"thread_id": "thread"}}
    configs = [
        base,
        {"configurable": {"thread_id": "thread", "checkpoint_id": "id"}},
        {"configurable": {"thread_id": "thread", "checkpoint_ns": "subgraph"}},
    ]
    transport = httpx.MockTransport(respond)
    url = "http://test.invalid"
    if async_mode:
        async with httpx.AsyncClient(base_url=url, transport=transport) as client:
            graph = RemoteGraph("graph", client=LangGraphClient(client))
            for config in configs:
                await graph.aget_state(config)
    else:
        with httpx.Client(base_url=url, transport=transport) as client:
            graph = RemoteGraph("graph", sync_client=SyncLangGraphClient(client))
            for config in configs:
                graph.get_state(config)

    assert requests == [
        ("GET", "/threads/thread/state"),
        ("POST", "/threads/thread/state/checkpoint"),
        ("POST", "/threads/thread/state/checkpoint"),
    ]
