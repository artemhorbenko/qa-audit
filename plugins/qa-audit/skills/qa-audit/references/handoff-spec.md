# Hand-off for AI agents (`qa-handoff.md`)

The report is for people; the hand-off is for the coding agent (Claude Code, Cursor, Codex…) that will implement the fixes. Same findings, same ids (BUG-01 = #1 in the report), written so an agent that never saw the report can act. `scripts/build_handoff.py` renders it from `audit.json`; `build_report.py` calls it.

## Shape

1. **YAML front matter**: `type: qa-handoff`, `schema: 1`, site, environment, deploy, audited, verdict (`blocks-release` / `fix-before-next-deploy` / `fix-in-backlog` / `ready`), stack, tasks count and by severity, not-checked areas, tests folder and run command.
2. **Rules for the agent**: order, one commit per BUG id, no real submits or production analytics events, ask before `decision` tasks, verify `hypothesis` tasks first, done = threshold + test, rerun the suite.
3. **Tasks table**: id, severity, area, observed/hypothesis, owner, test, title.
4. **Tasks grouped by owner**: `code` (agent can change it in the repo), `admin` (needs an admin UI: CMS, GTM, GA4, Search Console, hosting), `decision` (needs the owner's answer or wording). Each task: title, type and ICE, where (url / selector / file / template / plugin / setting / tool), environment, reproduce steps, expected, actual, evidence as text, fix steps, suggested change (code block), options considered, done when, test with its `QA_ONLY` command, owner action, risk, pre-mortem.
5. **Post-deploy checklist** as a task list, **tests table**, **sources used**.

No icons, colours, tooltips or persuasive headings; one fact per line; text in the language of `audit.json` (write it in English when the implementing team or agent works in English).

## What to put in audit.json for a good hand-off

- `bugs[].where`: be exact. A selector the agent can grep for, the file or template, the plugin and setting, or the admin screen path (`GA4 → Admin → Events → Key events`).
- `detail[].owner`: `code`, `admin` or `decision`. Mark it `decision` whenever the fix needs a business fact (copy, prices, which language versions or pages stay).
- `detail[].code` + `codeLang`: the snippet, rule or config to apply. Prefer a complete replacement (the whole robots.txt, the whole redirect rule) over a description.
- `stack`: what you detected; say "inferred" when you deduced it (from file names, hosts) rather than saw it.
