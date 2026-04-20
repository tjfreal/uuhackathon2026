# Publishing Topolski Explorer

This project is being prepared for public sharing from inside a larger hackathon repo.

The public version should demonstrate a real indexing and retrieval method over the
Topolski collection without redistributing the original source scans or relying on a bulky
checked-in vector store.

## The Working Split

Keep local:

- `staged_data_raw/`
- `data/staged/`
- `data/regions/`
- `data/chroma/`
- `.env`

These contain:

- original PDFs and source metadata
- rendered page images
- live transcription outputs under active generation
- crop images
- the local vector store

Safe public candidates:

- code
- docs
- feature manifest
- layout manifest
- processing matrix
- evaluation files
- selected sample manifests used for comparison work

Maybe-public later, only by deliberate choice:

- page-level transcription JSON snapshots

Those are more compelling than a pure skeleton, but they should be published only if the
project is consciously taking the "derived index over a public collection" route.

## Current Recommendation

Prefer a repo that says:

- here is the code
- here is the documented pipeline
- here are the derived structured artifacts
- here is how to regenerate the local vector index

That is stronger than a bare skeleton and cleaner than committing the live Chroma store.

## Export Workflow

Use:

```bash
python scripts/export_public_artifacts.py
```

This copies selected derived artifacts from `data/` into `published_artifacts/` without
touching the live working directories used by the background runs.

The export script currently copies:

- `feature_manifest.json`
- `layout_manifest.json`
- `region_eval_sample.json`
- `region_crop_manifest_sample.json`
- `region_transcription_manifest_sample.json`
- a sanitized per-item assessment library under `published_artifacts/artifact_library/`
- `artifact_library_manifest.json`

It does **not** export:

- original PDFs
- page images
- crop images
- ChromaDB
- full staged transcription outputs
- the live processing matrix artifacts

## GitHub Read

The intended public repo shape is:

- inspectable code
- inspectable derived metadata
- rebuildable local search index
- no raw collection redistribution

That makes the project read less like a skeleton and more like a real indexing and
retrieval layer over a public archive.

## Rebuild Path

After exporting the public artifact library, rebuild a local index with:

```bash
python pipeline/12_embed_published_artifacts.py
```

That script reads the sanitized assessment JSON in `published_artifacts/artifact_library/`
and builds a local Chroma index without needing the original PDFs or page images.
