---
description: "Use when running Python commands, installing packages, starting the backend server, or executing tests. Ensures the .venv virtual environment is activated first."
applyTo: "backend/**"
---

# Python Virtual Environment

This project uses a Python virtual environment located at `.venv` in the project root.

Before running any Python command in the terminal, activate the virtual environment first:

```bash
source .venv/bin/activate
```

This applies to all terminal operations including:

- Running the backend server (`uvicorn`)
- Installing Python packages (`pip install`)
- Running tests (`pytest`)
- Any `python3` or `python` commands
