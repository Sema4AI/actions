from sema4ai.actions import action


@action
def action_with_agent_headers() -> str:
    from sema4ai.actions.chat import _get_client_and_thread_id

    _client, thread_id = _get_client_and_thread_id()
    return f"thread_id: {thread_id}"
