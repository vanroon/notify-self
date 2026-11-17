from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows.client import get_mistral_client

with workflows.workflow.unsafe.imports_passed_through():
    import httpx

DEFAULT_TOPIC = "Q5O35G4XC3WF"
POEM_MODEL = "mistral-small-latest"


class PoemInput(BaseModel):
    theme: str = "something small and beautiful"
    topic: str = DEFAULT_TOPIC


class PoemOutput(BaseModel):
    poem: str
    topic: str
    delivered: bool


@workflows.activity()
async def write_poem(theme: str) -> str:
    """Generate a short poem with Mistral."""
    client = get_mistral_client()
    response = await client.chat.complete_async(
        model=POEM_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a short poem of 4 to 8 lines about {theme}. "
                    "Respond with the poem only: no title, no quotes, no commentary."
                ),
            }
        ],
    )
    poem = (response.choices[0].message.content or "").strip()
    if not poem:
        raise RuntimeError("The model returned an empty poem")
    return poem


@workflows.activity()
async def send_to_ntfy(poem: str, topic: str) -> bool:
    """Publish the poem as an ntfy.sh push notification."""
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.post(
            f"https://ntfy.sh/{topic}",
            content=poem.encode("utf-8"),
            headers={
                "Title": "A poem for you",
                "Tags": "scroll",
            },
        )
        response.raise_for_status()
    return True


@workflows.workflow.define(
    name="poem-to-phone",
    workflow_display_name="Poem to Phone",
    workflow_description="Writes a short poem with Mistral and sends it to your phone via ntfy.sh.",
)
class PoemToPhoneWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: PoemInput) -> PoemOutput:
        poem = await write_poem(input.theme)
        delivered = await send_to_ntfy(poem, input.topic)
        return PoemOutput(poem=poem, topic=input.topic, delivered=delivered)
