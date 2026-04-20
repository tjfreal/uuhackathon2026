# Published Artifacts

This directory is the intended home for shareable derived outputs.

It should contain only artifacts that are safe and useful to publish:

- structured manifests
- evaluation fixtures
- sample comparison outputs

It should not contain:

- original PDFs
- rendered page images
- region crops
- the live Chroma index
- `.env` or runtime state

Populate this directory with:

```bash
python scripts/export_public_artifacts.py
```

That export is designed to copy selected derived artifacts out of the ignored `data/`
tree without disturbing any active background processing.
