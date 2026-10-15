---
name: story
description: "Write Azure DevOps work items and put them on the board: user stories, issues and bugs in Markdown, split into items that each ship on their own, with descriptions a person or an agent can pick up cold and acceptance criteria that an engineer, QA, a PM and the client can each check, placed under the right parent, area path and current iteration. Use when asked to write, create, file, split, size, refine or rewrite a user story, bug, backlog item or acceptance criteria, or to turn a request, ticket or wish list into backlog work, even when Azure DevOps is not named. Not for logging time against a work item (tt), a pull request description or review threads (pull-request), or a spec and implementation plan in the repository (spec)."
---

# Story

Role: worker. Loaded by the session or subagent that writes Azure DevOps work items; this file
stays under about 120 lines.

## Procedure

1. **Look first, read-only.** Before proposing anything, read the team's settings and current
   iteration, the open Epics and Features, and the stories changed in the last few months (area
   path, iteration, parent, title, state). Look for an item that already covers the request,
   closed ones included: propose refining or linking it (step 6) instead of filing a duplicate.
   Place new items the way those siblings are placed: their parent Feature, their area path, the
   team's current iteration path as returned, their title convention.
2. **Pick the type.** User Story for anything a user can see or do. Issue for technical work with
   no user-facing change, only where the team's stories backlog lists Issue beside User Story
   (the backlog levels say which types each level holds). In the stock Agile process an Issue is
   an impediment, off the backlog and without Story Points, so there technical work is a User
   Story. Bug only when existing behaviour is broken; a capability that never existed is a User
   Story even when the requester asks for a bug, and the answer says why. Read the type's fields
   before writing: a type with no Acceptance Criteria field takes its criteria under
   `### Acceptance Criteria` in the Description.
3. **Break it down.** One item is one outcome a user or the client can accept on its own.
   - A request with several outcomes becomes one story per outcome, even when the requester asks
     for one item: sibling stories under the parent found in step 1, if any. A new Feature or
     anything above a story only when the requester asks for one. Never split by technical layer.
   - An item that waits on other work gets a predecessor link and a later iteration.
   - Estimate in Fibonacci story points: 1, 2, 3, 5, 8, 13. Map anyone's 6 or 7 to the nearest
     value. Above 13, split along parts that ship separately and estimate each.
4. **Write the description** (template below) so that a person or an agent who has seen neither
   this conversation nor the client's ticket can do the work: copy every fact from the ticket or
   its attachment into the item, and keep the link.
5. **Write the acceptance criteria** (template below).
   - Each criterion is something a person sees or does in the product, in its users' words
     (screens, roles, buttons, messages), with exact numbers and messages, so an engineer, QA, a
     PM and the client reach the same verdict.
   - Engineering done-ness stays out: field or API names, code, flows, tests and coverage,
     deployment steps. Those go under Technical Notes in the description.
   - One criterion per rule, exception and fallback in the request; no "works correctly",
     "is fast", "handles errors gracefully".
6. **Propose, then write.** Show the drafts and where each goes; write once the requester agrees.
   A request to put it on the board is that agreement, unless you split it or would refine or
   link an existing item instead: then propose the items or the change (which item, what
   changes), say why, and write nothing until the requester confirms.
   - Send the Markdown format flag on every rich-text field (Description, Acceptance Criteria,
     Repro Steps, System Info) in every create and update, also when the field holds HTML
     today. Never on Title, Tags or other single-line fields, which reject it. A write call
     with no format field (for example, the self-hosted server's single-item update when this
     was written) can't do this: use one that has it, such as that server's batch update with
     one item.
   - Link each new item to its parent (link type `parent`) unless it was created as a child.
   - Read each item back and check format, area, iteration and parent; report id, title,
     placement and link.

## Templates

No bold fragments inside sentences; use the headings.

User Story description (an Issue opens with `We need <capability> to <purpose>.` instead, with
"to", not "so that"):

```markdown
As a <role>, I want <capability> so that <benefit>.

#### Additional Context

Who asked, why now, and every fact from the ticket written out (lists, numbers,
messages). Ticket: <link>

#### Out of Scope

- <what the request rules out>

#### Technical Notes

<approach, objects and field names, tests, deployment path>

#### Dependencies

<items this waits on, or None>
```

Acceptance criteria:

```markdown
### 1. <Area of behaviour>

- [ ] <Who> <does or sees what> when <condition>.
- [ ] Error "<exact message>" shows when <condition>.

### 2. <Next area>

- [ ] ...
```

A Bug puts `### Steps to Reproduce`, `### Expected Behavior` and `### Actual Behavior` in Repro
Steps (`Microsoft.VSTS.TCM.ReproSteps`), the environment in System Info
(`Microsoft.VSTS.TCM.SystemInfo`), and sets Severity and Priority to the process's full values
(Severity `2 - High`, not `High`); its Description stays empty.
