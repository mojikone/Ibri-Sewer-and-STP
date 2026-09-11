---
name: list-tasks-before-multistep-work
description: "Before a multi-step job (several scripts, layers, docs), list the tasks and wait for approval; do not start on \"clear?\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4c6c2c7b-00c3-4e9a-b8fc-2e647a78c88a
  modified: 2026-09-09T21:09:09.933Z
---

When a job has several steps (new layers, growth model, boundaries, docs), list the tasks first and start only after the engineer approves. "Clear?" at the end of a rule discussion is a check of understanding, not a go.

**Why:** On 2026-09-09 I confirmed the rules and immediately opened the workbook; the engineer interrupted: "first list the tasks, then go upon approval." He works remotely and wants to see the plan before the repo changes.

**How to apply:** Reply "clear" plus a numbered task list with what each produces, then stop. Go when he says go. Related: [[show-drawings-not-tables]], [[response-depth-auto-default]].
