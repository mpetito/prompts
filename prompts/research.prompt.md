---
name: research
description: Conduct deep technical research and option evaluation on a topic, library, or API
---

# Research

Research the topic provided below within the context of the current codebase.

Follow the `research` skill:

1. **Contextualize**: find existing usage in the codebase, capture stack/constraints
2. **Gather**: pull from official docs (`docs-context7`), reasoning/deep search (`perplexity`), GitHub issues and code, and web sources — fanning out to subagents for parallel topics
3. **Synthesize**: cross-reference, flag contradictions or stale info, adapt findings to our codebase

Produce the standard research output: key findings, codebase context, options analysis with pros/cons, a recommendation with implementation notes, code examples, and cited references.

Suggest `/spec` (to turn findings into a spec + plan) or direct implementation as the next step.

## User Input

```text
$ARGUMENTS
```
