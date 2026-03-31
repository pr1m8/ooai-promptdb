# Testing

The scaffold separates tests into three layers.

## Unit

```bash
pdm run pytest -m unit
```

Fast, isolated tests for domain logic, file helpers, and CLI behavior.

## Integration

```bash
pdm run pytest -m integration
```

These cover service, persistence, alias movement, and export flows.

## End-to-end

```bash
pdm run pytest -m e2e
```

These exercise the FastAPI boundary with realistic request and response payloads.
