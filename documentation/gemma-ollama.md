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
OLLAMA_MODEL=gemma3:1b
OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_NUM_PREDICT=350
OLLAMA_NUM_CTX=2048
OLLAMA_KEEP_ALIVE=1m
```

The exact model name must match what is installed in Ollama.


## CPU-only laptop guidance

Your current laptop can run Gemma locally, but it does not have a dedicated NVIDIA GPU. That means Ollama may use the CPU, which can make the laptop hot and make generation feel stuck.

Recommended defaults for this project:

```text
OLLAMA_MODEL=gemma3:1b
OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_NUM_PREDICT=350
OLLAMA_NUM_CTX=2048
OLLAMA_KEEP_ALIVE=1m
```

If the machine still gets hot, use:

```text
OLLAMA_NUM_PREDICT=200
OLLAMA_TIMEOUT_SECONDS=45
```

The deterministic report does not require Gemma. You can always run:

```bash
python -m app.main analyze AAPL
```

Use Gemma only when you want a natural-language explanation of that report.

## Stop a stuck local model

In the terminal, press `Ctrl+C` if the command is still running. To ask Ollama to unload the model from memory, run:

```powershell
Invoke-RestMethod -Uri http://localhost:11434/api/generate -Method Post -ContentType "application/json" -Body '{"model":"gemma3:1b","prompt":"","keep_alive":0}'
```

As a last resort on Windows, stop Ollama completely:

```powershell
taskkill /F /IM ollama.exe
```

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
