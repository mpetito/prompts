# Skill authoring best practices (Anthropic, platform.claude.com, fetched 2026-10-10)

Source: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

Good Skills are concise, well-structured, and tested with real usage.

## Core principles

### Concise is key

The context window is a public good. Your Skill shares the context window with the system prompt, conversation history, other Skills' metadata and the actual request. At startup only the metadata (name and description) from all Skills is pre-loaded. Claude reads SKILL.md only when the Skill becomes relevant, and additional files only as needed. Being concise in SKILL.md still matters: once loaded, every token competes with conversation history and other context.

**Default assumption: Claude is already very smart.** Only add context Claude doesn't already have. Challenge each piece of information: "Does Claude really need this explanation?" "Can I assume Claude knows this?" "Does this paragraph justify its token cost?"

Good (about 50 tokens): a heading, one sentence naming the library, and a short code block. Bad (about 150 tokens): explaining what a PDF is, that libraries exist, that one is recommended because it is easy, and that it must be installed first.

### Set appropriate degrees of freedom

Match the level of specificity to the task's fragility and variability.

- **High freedom** (text instructions): multiple approaches are valid, decisions depend on context, heuristics guide the approach. Example: a code review process listed as four numbered activities.
- **Medium freedom** (pseudocode or scripts with parameters): a preferred pattern exists, some variation is acceptable, configuration affects behavior.
- **Low freedom** (specific scripts, few or no parameters): operations are fragile and error-prone, consistency is critical, a specific sequence must be followed. Example: "Run exactly this script: `python scripts/migrate.py --verify --backup`. Do not modify the command or add additional flags."

Analogy: a narrow bridge with cliffs on both sides needs exact instructions; an open field needs general direction.

### Test with all models you plan to use

Skills are additions to models. Haiku: does the Skill provide enough guidance? Sonnet: is it clear and efficient? Opus: does it avoid over-explaining? Aim for instructions that work across the models you use.

## Skill structure

### Naming conventions

Consider gerund form (`processing-pdfs`, `analyzing-spreadsheets`). Acceptable alternatives: noun phrases (`pdf-processing`) and action-oriented (`process-pdfs`). Avoid vague names (`helper`, `utils`, `tools`), overly generic ones (`documents`, `data`, `files`), reserved words (`anthropic-helper`, `claude-tools`), and inconsistent patterns within your collection. `name` must be lowercase letters, numbers and hyphens.

### Writing effective descriptions

The `description` enables discovery and should include both what the Skill does and when to use it. Be specific and include key terms and specific triggers/contexts. Claude uses it to choose among potentially 100+ Skills. Effective examples:

- `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.`
- `Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.`
- `Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.`

Avoid vague descriptions: "Helps with documents", "Processes data", "Does stuff with files".

### Progressive disclosure patterns

SKILL.md is an overview that points Claude to detailed materials as needed, like a table of contents. Keep the SKILL.md body under 500 lines; split content into separate files when approaching the limit.

- **Pattern 1, high-level guide with references:** SKILL.md holds the quick start; FORMS.md, REFERENCE.md and EXAMPLES.md are loaded only when needed.
- **Pattern 2, domain-specific organization:** for multi-domain Skills, `reference/finance.md`, `reference/sales.md` and so on, so a sales question never loads finance schemas. SKILL.md can suggest `grep -i "revenue" reference/finance.md` to find a metric.
- **Pattern 3, conditional details:** show basic content and link to advanced content ("For tracked changes: see REDLINING.md").

### Avoid deeply nested references

Claude may partially read files referenced from other referenced files (for example with `head -100`). **Keep references one level deep from SKILL.md.** All reference files should link directly from SKILL.md. Bad: SKILL.md links advanced.md, which links details.md, which holds the information.

### Structure longer reference files with a table of contents

For reference files longer than 100 lines, include a table of contents at the top, so the full scope is visible even in a partial read.

## Workflows and feedback loops

### Use workflows for complex tasks

Break complex operations into clear, sequential steps. For particularly complex workflows, provide a checklist Claude can copy into its response and check off as it progresses (for example "Research Progress: Step 1 read all sources, Step 2 identify themes, Step 3 cross-reference claims, Step 4 structured summary, Step 5 verify citations", with a paragraph per step). Works for analysis tasks without code and for script-driven tasks (analyze_form.py, then edit fields.json, then validate_fields.py, then fill_form.py, then verify_output.py; if verification fails return to step 2). Clear steps prevent skipping critical validation.

### Implement feedback loops

Common pattern: run validator, fix errors, repeat. This greatly improves output quality. Without code, the "validator" can be a reference document such as STYLE_GUIDE.md that Claude checks against: draft, review against the checklist, note each issue with a section reference, revise, review again, proceed only when all requirements are met. With code: edit, validate immediately with a script, fix until validation passes, then rebuild and test the output.

## Content guidelines

### Avoid time-sensitive information

Don't include information that will become outdated ("if you're doing this before August 2025 use the old API"). Instead keep a "Current method" section and an "Old patterns" section, with deprecated material in a collapsed `<details>` block that names when it was deprecated.

### Use consistent terminology

Choose one term and use it throughout. Good: always "API endpoint", always "field", always "extract". Bad: mixing "API endpoint", "URL", "API route", "path"; or "field", "box", "element", "control"; or "extract", "pull", "get", "retrieve".

## Common patterns

### Template pattern

Provide templates for output format, matching strictness to need. For strict requirements: "ALWAYS use this exact template structure" with a fixed markdown skeleton. For flexible guidance: "Here is a sensible default format, but use your best judgment", with the skeleton marked as adaptable.

### Examples pattern

Where output quality depends on seeing examples, provide input/output pairs, as in regular prompting (for example three commit-message examples, then "Follow this style: type(scope): brief description, then detailed explanation"). Examples convey style and level of detail more clearly than descriptions.

### Conditional workflow pattern

Guide Claude through decision points: "Creating new content? Follow the creation workflow. Editing existing content? Follow the editing workflow", each with its own steps.

## Evaluation and iteration

### Build evaluations first

Create evaluations before writing extensive documentation. Evaluation-driven development: identify gaps by running Claude on representative tasks without the Skill and documenting failures; create three scenarios that test these gaps; establish a baseline without the Skill; write minimal instructions that address the gaps and pass the evaluations; iterate. Evaluation structure: `{"skills": [...], "query": "...", "files": [...], "expected_behavior": ["...", "..."]}`.

### Develop Skills iteratively with Claude

Work with one Claude ("Claude A") to create a Skill used by other instances ("Claude B"). Complete a task without a Skill and notice what context you repeatedly provide; identify the reusable pattern; ask Claude A to create the Skill; review for conciseness ("remove the explanation about what win rate means"); improve information architecture (move schemas to a reference file); test with Claude B on similar tasks; iterate from observation ("Claude B forgot to filter by date for Q4"). Continue the observe-refine-test cycle on real workflows. Gather team feedback: does the Skill activate when expected, are instructions clear, what is missing.

### Observe how Claude navigates Skills

Watch for unexpected exploration paths (structure not intuitive), missed connections (links not explicit enough), overreliance on certain sections (content that belongs in SKILL.md), and ignored content (unnecessary or poorly signaled files). The `name` and `description` are particularly critical for triggering.

## Anti-patterns to avoid

### Avoid Windows-style paths

Always use forward slashes: `scripts/helper.py`, never `scripts\helper.py`.

### Avoid offering too many options

Don't present multiple approaches unless necessary. Bad: "You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or…". Good: provide a default with an escape hatch: "Use pdfplumber for text extraction. For scanned PDFs requiring OCR, use pdf2image with pytesseract instead."

## Advanced: Skills with executable code

### Solve, don't defer

Handle error conditions in scripts rather than deferring to Claude: catch a missing file and create a default, catch a permission error and provide an alternative, instead of "just fail and let Claude figure it out". Configuration parameters should be justified and documented to avoid "voodoo constants" (Ousterhout's law): `REQUEST_TIMEOUT = 30` with a comment explaining why, not `TIMEOUT = 47  # Why 47?`.

### Provide utility scripts

Pre-made scripts are more reliable than generated code, save tokens (their contents never enter context), save time and ensure consistency. Make clear whether Claude should **execute** the script ("Run `analyze_form.py` to extract fields", the common case) or **read it as reference** ("See `analyze_form.py` for the field extraction algorithm"). Document each script with its command line and output format.

### Use visual analysis

When inputs can be rendered as images, convert them and have Claude analyze the images.

### Create verifiable intermediate outputs

For complex, open-ended tasks use plan-validate-execute: create a plan in a structured file, validate it with a script, then execute, then verify. Catches errors early, is machine-verifiable, keeps planning reversible, and gives clear debugging. Use for batch operations, destructive changes, complex validation rules, high-stakes operations. Make validation scripts verbose with specific messages ("Field 'signature_date' not found. Available fields: …").

### Package dependencies

Skills run in a code execution environment with platform limits (claude.ai can install from npm, PyPI and GitHub; the API has no network and no runtime installation). List required packages in SKILL.md and verify availability.

### Runtime environment

Metadata is pre-loaded; files are read on demand with bash or Read; scripts execute without loading their contents; large files cost nothing until read. Use forward slashes; name files descriptively (`form_validation_rules.md`, not `doc2.md`); organize directories by domain or feature; bundle comprehensive resources; prefer scripts for deterministic operations; make execution intent clear; test file access patterns with real requests.

### MCP tool references

Use fully qualified tool names, `ServerName:tool_name` (for example `BigQuery:bigquery_schema`, `GitHub:create_issue`), so the tool is found when several servers are available.

### Avoid assuming tools are installed

Be explicit about dependencies: "Install required package: `pip install pypdf`", then the usage, rather than "use the pdf library".

## Technical notes

- `name`: maximum 64 characters, lowercase letters, numbers and hyphens only, no XML tags, no reserved words.
- `description`: maximum 1,024 characters, non-empty, no XML tags.
- Keep the SKILL.md body under 500 lines; split into separate files beyond that.

## Checklist for effective Skills

Core quality:
- Description is specific and includes key terms
- Description includes both what the Skill does and when to use it
- SKILL.md body is under 500 lines
- Additional details are in separate files (if needed)
- No time-sensitive information (or in an "old patterns" section)
- Consistent terminology throughout
- Examples are concrete, not abstract
- File references are one level deep
- Progressive disclosure used appropriately
- Workflows have clear steps

Code and scripts:
- Scripts solve problems rather than defer to Claude
- Error handling is explicit and helpful
- No "voodoo constants" (all values justified)
- Required packages listed in instructions and verified as available
- Scripts have clear documentation
- No Windows-style paths (all forward slashes)
- Validation/verification steps for critical operations
- Feedback loops included for quality-critical tasks

Testing:
- At least three evaluations created
- Tested with Haiku, Sonnet, and Opus
- Tested with real usage scenarios
- Team feedback incorporated (if applicable)
