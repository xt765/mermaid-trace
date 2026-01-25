# User Guide

## Introduction

MermaidTrace bridges the gap between code execution and architectural visualization. Unlike static analysis tools, it traces *actual* runtime calls, giving you a true picture of your system's behavior.

## How It Works

1.  **Decorate**: You place `@trace` on functions you want to appear in the diagram.
2.  **Intercept**: When the function runs, MermaidTrace logs a "Request" event (`->>`).
3.  **Execute**: The function body executes.
4.  **Return**: MermaidTrace logs a "Return" event (`-->>`) with the return value.
5.  **Visualize**: The events are written to a `.mmd` file, which renders as a sequence diagram.

## Context Inference

One of the most powerful features is **Context Inference**.

In a sequence diagram, every arrow has a `Source` and a `Target`.
- `Target` is easy: it's the function/class being called.
- `Source` is hard: it's *who called* the function.

MermaidTrace uses Python's `contextvars` to track the "Current Participant".

**Example:**
1.  `A` calls `B`.
2.  Inside `A`, the context is set to "A".
3.  When `B` is decorated with `@trace`, it sees the context is "A", so it draws `A ->> B`.
4.  Inside `B`, the context is updated to "B".
5.  If `B` calls `C`, `C` sees the context is "B", so it draws `B ->> C`.

This means you usually only need to set the `source` on the *entry point* (the first function).

## CLI Viewer

To view your diagrams, use the CLI:

```bash
mermaid-trace serve flow.mmd --port 8000
```

This starts a local server and opens your browser. It auto-refreshes when you reload the page.
