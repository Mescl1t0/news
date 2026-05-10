# OpenClaw-native AI enrichment

This project does not require an external OpenAI API key.

The deterministic scripts handle fetch, normalize, render, validate, and archive updates. The AI step is intentionally performed by the OpenClaw agent using the active OpenClaw subscription/session.

## Workflow

### 1. Prepare data for AI

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode prepare-ai
```

This creates:

- `public/reports/YYYY-MM-DD/raw.json`
- `public/reports/YYYY-MM-DD/normalized.json`

Then the pipeline stops.

### 2. OpenClaw agent writes enriched.json

The agent reads:

- `public/reports/YYYY-MM-DD/normalized.json`

The agent writes:

- `public/reports/YYYY-MM-DD/enriched.json`

For every item, the agent must fill:

- `title_ru` — natural Russian headline
- `description_ru` — exactly one neutral Russian sentence

Rules:

- Preserve `id`, `section_id`, `position`, `url`, `source`, and `raw`.
- Do not invent new items.
- Do not add metadata to visible content.
- Keep descriptions neutral and factual.
- Set:

```json
"enrichment": {
  "used_llm": true,
  "provider": "openclaw-agent"
}
```

### 3. Publish from enriched data

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode publish-ai
```

This creates/updates:

- `public/reports/YYYY-MM-DD/index.html`
- `public/index.html`

It also runs validation.

## Fallback mode

For testing only:

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode full-fallback
```

This does not call AI and does not translate content. It only ensures the static renderer can work without the agent step.
