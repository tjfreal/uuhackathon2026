# Outputs

This directory is for committed example output from `askme.py`.

Expected files:
- `example-prompts.md` — default top `N` prompt output
- `people-gaps.md` — people-only prompt output
- `gaps.json` — JSON-formatted ranked gaps

Regenerate from the repo root with:

```bash
mkdir -p outputs
python askme.py --index-dir ~/note-system/.index --n 5 --out outputs/example-prompts.md
python askme.py --index-dir ~/note-system/.index --type people --n 5 --out outputs/people-gaps.md
python askme.py --index-dir ~/note-system/.index --format json --n 5 --out outputs/gaps.json
```

These files should be refreshed whenever output formatting, ranking, or gap detection changes in a user-visible way.
