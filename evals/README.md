# Evals

- `evals.json` - end-to-end scenarios: what a run must do (`expectations`) and must not do (`forbidden`). Run each in a fresh session with the plugin installed, then grade the result against the lists.
- `trigger-evals.json` - prompts that should and should not start the skill (QA vs product strategy is the main boundary).
- `results.md` - one row per run. Real sites stay private: record the scenario and the scores, not the site's name or data.
- `runner-fixture/` - a tiny local site and suite that exercise every runner check type, including ones that must fail:

```
cd evals/runner-fixture/site && python3 -m http.server 8765 &
cp -r ../../plugins/qa-audit/skills/qa-audit/assets/qa-tests /tmp/qt && cp ../qa-suite.json /tmp/qt/
cd /tmp/qt && npm i && npx playwright install chromium && npx playwright test --retries=0
# expected: F03, F06x, F11, F12 fail; everything else passes
```

Every report must also pass:

```
python plugins/qa-audit/skills/qa-audit/scripts/validate_audit.py audit.json
python plugins/qa-audit/skills/qa-audit/scripts/check_report.py report.html
```
