# OpenClaw-native AI enrichment

This project does not require an external OpenAI API key.

The deterministic scripts handle fetch, normalize, compact AI input generation, merge, render, validate, and archive updates. The AI step is performed by the OpenClaw agent using the active OpenClaw subscription/session.

## Workflow

### 1. Prepare compact data for AI

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode prepare-ai
```

This creates:

- `public/reports/YYYY-MM-DD/raw.json`
- `public/reports/YYYY-MM-DD/normalized.json`
- `public/reports/YYYY-MM-DD/ai_input.json`

Then the pipeline stops.

### 2. OpenClaw agent writes compact ai_output.json

The agent reads:

- `public/reports/YYYY-MM-DD/ai_input.json`

The agent writes:

- `public/reports/YYYY-MM-DD/ai_output.json`

Output schema:

```json
{
  "provider": "openclaw-agent",
  "items": [
    {
      "id": "same id from ai_input",
      "title_ru": "natural Russian headline",
      "description_ru": "exactly one neutral Russian sentence"
    }
  ]
}
```

Rules:

- Preserve every item `id`.
- Do not invent new items.
- Do not add URLs or metadata to AI output.
- Keep descriptions neutral and factual.
- Use exactly one Russian sentence for `description_ru`.

### 3. Merge and publish

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode publish-ai
```

This creates/updates:

- `public/reports/YYYY-MM-DD/enriched.json`
- `public/reports/YYYY-MM-DD/index.html`
- `public/index.html`
- `public/archive.html`

It also runs validation.

## Fallback mode

For testing only:

```bash
python3 tools/build_report.py --date YYYY-MM-DD --mode full-fallback
```

This does not call AI and does not translate content. It only ensures the static renderer can work without the agent step.
