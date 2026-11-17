import pytest
from temporalio.testing import WorkflowEnvironment


@pytest.fixture(autouse=True)
def _no_otel_trace_upsert(monkeypatch):
    monkeypatch.setattr(
        "mistralai.workflows.core.workflow.set_otel_trace_id_in_current_workflow_execution",
        lambda: None,
        raising=False,
    )


@pytest.fixture
async def temporal_env():
    env = await WorkflowEnvironment.start_time_skipping()
    try:
        yield env
    finally:
        await env.shutdown()
