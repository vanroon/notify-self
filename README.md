# poem-notify

A Mistral Workflow that writes a short poem and sends it to your phone as a
push notification via [ntfy.sh](https://ntfy.sh).

## Workflow

`poem-to-phone` — input:

| Field   | Type | Default                          | Description                     |
| ------- | ---- | -------------------------------- | ------------------------------- |
| `theme` | str  | `"something small and beautiful"` | What the poem should be about  |
| `topic` | str  | `Q5O35G4XC3WF`                    | ntfy.sh topic to publish to    |

Output: `{ "poem": "...", "topic": "...", "delivered": true }`.

Subscribe to `https://ntfy.sh/Q5O35G4XC3WF` in the ntfy app to receive the
notifications.

## Project layout

```
apps/worker/               Python worker package (Workflows SDK)
├── src/worker/
│   ├── entrypoints/worker.py   worker entrypoint, discovers workflows
│   └── workflows/poem.py       poem-to-phone workflow + activities
└── tests/                      local tests (temporal test env, mocked externals)
deploy/docker/Dockerfile.worker   image built by managed deployments
```

## Local development

```bash
cd apps/worker
uv sync --extra dev
cp ../../.env.example ../../.env   # then set MISTRAL_API_KEY
uv run pytest
```

Run the worker locally with the Mistral CLI: `mistral dev` from the project
root (needs `MISTRAL_API_KEY` in `.env`).

## Deployment

Managed deployments build `deploy/docker/Dockerfile.worker` from the
repository root. No secrets are needed in the image: the worker
authenticates with the platform-injected service-account token.
