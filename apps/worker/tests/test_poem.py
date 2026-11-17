from types import SimpleNamespace

import httpx

import mistralai.workflows as workflows
from mistralai.workflows.testing import DEFAULT_TEST_TASK_QUEUE, create_test_worker

from worker.workflows import poem as poem_module
from worker.workflows.poem import PoemInput, PoemToPhoneWorkflow, send_to_ntfy, write_poem

POEM = "small things glow\nwhen no one watches"


class FakeChat:
    async def complete_async(self, model, messages):
        self.model = model
        self.messages = messages
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=f"  {POEM}\n"))]
        )


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


async def test_write_poem_strips_model_output(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(poem_module, "get_mistral_client", lambda: fake)

    result = await write_poem("rain on a tin roof")

    assert result == POEM
    assert fake.chat.model == poem_module.POEM_MODEL
    assert "rain on a tin roof" in fake.chat.messages[0]["content"]


async def test_send_to_ntfy_posts_poem(monkeypatch):
    sent = []

    async def fake_post(self, url, content=None, headers=None):
        sent.append((url, content, headers))
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    delivered = await send_to_ntfy(POEM, "test-topic")

    assert delivered is True
    url, content, headers = sent[0]
    assert url == "https://ntfy.sh/test-topic"
    assert content.decode("utf-8") == POEM
    assert headers["Title"] == "A poem for you"


async def test_poem_to_phone_workflow(temporal_env, monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(poem_module, "get_mistral_client", lambda: fake)
    sent = []

    async def fake_post(self, url, content=None, headers=None):
        sent.append((url, content, headers))
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    workflows.config.temporal.task_queue = DEFAULT_TEST_TASK_QUEUE

    async with create_test_worker(
        temporal_env,
        [PoemToPhoneWorkflow],
        activities=[write_poem, send_to_ntfy],
        task_queue=DEFAULT_TEST_TASK_QUEUE,
    ):
        result = await temporal_env.client.execute_workflow(
            "poem-to-phone",
            PoemInput(theme="rain on a tin roof", topic="test-topic").model_dump(),
            id="poem-to-phone-test",
            task_queue=DEFAULT_TEST_TASK_QUEUE,
        )

    assert result["poem"] == POEM
    assert result["topic"] == "test-topic"
    assert result["delivered"] is True
    assert sent[0][0] == "https://ntfy.sh/test-topic"
