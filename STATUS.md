# Status

Living state of the work. Update at the end of every session. Public repo: no real site names, client data or private links here.

**Version:** 1.1.0 (2026-11-24)

## Done recently

- 1.1.0: hand-off file for AI coding agents (`qa-handoff.md`, `build_handoff.py`, `references/handoff-spec.md`), tasks grouped by owner (code / admin / decision) with location, fix code, done-when and test.
- Test runner aborts every analytics and ad hit, so synthetic events never reach production data; new checks `tag_present` and `robots_disallow`; `form_event` supports Gravity Forms (jQuery events).
- SKILL.md: read the published GTM container, GA4 key events and Search Console's Pages report (all read-only) to close the analytics loop.
- Fixed `build_report.py` escaping `<!--` into invalid JSON.
- 1.0.0: skill, report template in the product-lens-audit design, generic Playwright runner with 15 check types, English demo (fictional), runner fixture.
- Test runs: WordPress logistics site after a redesign; B2B SaaS marketing site with GA4 and Search Console access. See `evals/results.md`.
- Repo docs: `CLAUDE.md`, `STATUS.md`.

## In progress

- Nothing open in this repo.

## Next

1. Re-check the second B2B SaaS run against the "production domain only" rule: its top finding covers a second host that may not be live production. Confirm with the maintainer, then drop or downgrade it in the private report and hand-off, and add a host check to SKILL.md step 1.
2. Maintainer: create git tags v1.0.0 and v1.1.0 and a GitHub Release (the session cannot push tags).
3. Run a generated suite against a live site from a machine that can reach it (local or CI), then fix selector drift and update `tests[].st` from real results.
4. Test in Claude Code desktop and in the Claude app (upload the ZIP); run the trigger evals from `evals/trigger-evals.json` with the skill-creator skill.
5. Open roadmap items: `qa-handoff.json`, `--handoff-lang`, and an eval in which an agent fixes the runner fixture from the hand-off alone.
6. Test on e-commerce (WooCommerce cart without checkout) and on a site with HubSpot forms.

## Open questions

- Should the WordPress QA service run `qa-suite.json` from a deploy hook or from scheduled CI?
- Is a public case study possible on a real site (owner consent needed)?
- Port the hand-off format back into product-lens-audit's shared core, or keep each skill's own?

## Links

- Public demo: EN https://claude.ai/artifact/4mXJrvNQ9Mb5NGobzLibgs (fictional "Harbourline Cargo"; the maintainer shares it publicly)
- Example hand-off: `docs/example-qa-handoff.md`
- Roadmap: `ROADMAP.md`
