# CLI Guide

The CLI uses Rich for tables, panels, JSON rendering, and readable local output.

## Commands

### `promptdb init`

Create a small local workspace:

```bash
promptdb init
promptdb init --root sandbox/project-x
```

### `promptdb list`

List stored prompt versions in a Rich table.

```bash
promptdb list
```

### `promptdb register-file`

Register a prompt from YAML, JSON, or plain text.

```bash
promptdb register-file prompts/support_assistant.yaml demo assistant --alias production
promptdb register-file prompts/raw.txt demo summary --kind string --alias latest
```

### `promptdb resolve`

Resolve a compact prompt reference.

```bash
promptdb resolve demo/assistant:production
promptdb resolve demo/assistant:rev:1
```

### `promptdb render`

Render a prompt with runtime variables.

```bash
promptdb render demo/assistant:production --var question="Where is my refund?"
```

### `promptdb export-file`

Write a resolved version bundle to disk.

```bash
promptdb export-file demo/assistant:production build/assistant.json
```
