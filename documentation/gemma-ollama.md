# Gemma and Ollama

## Role of Gemma in this project

Gemma is used as an explanation layer. It should not calculate indicators, fetch market data, or make unsupported claims. The current design sends Gemma a structured JSON quick report and asks it to explain the report carefully.

Correct role:

```text
Structured data -> Gemma explanation -> human review
```

Incorrect role:

```text
Prompt only -> unsupported trade decision
```

## Current integration file

```text
app/llm/ollama_client.py
```

## Configuration

The `.env` file controls:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT_SECONDS=120
```

The exact model name must match what is installed in Ollama.

## Check Ollama availability

```bash
python -m app.main doctor
```

## Analyze with Gemma

```bash
python -m app.main analyze AAPL --use-gemma
```

In the dashboard, enable:

```text
Use Gemma explanation
```

## Prompt design principle

Gemma receives structured data and should explain:

- bullish factors,
- bearish factors,
- uncertainty,
- risk considerations,
- what additional data would be needed.

It should not say that a trade is guaranteed.

## Future improvements

Later volumes can add:

- prompt templates as separate files,
- strict JSON output parsing,
- model response evaluation,
- citation-aware RAG,
- local document retrieval,
- multiple LLM providers,
- automated report generation.
