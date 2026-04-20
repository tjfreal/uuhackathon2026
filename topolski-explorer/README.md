# Topolski Explorer

Semantic search over the Topolski Chronicles — a collection of ~3,000 broadsheet issues
held by the Marriott Library at the University of Utah.

The collection mixes typeset text, Topolski's cramped handwritten annotations, and his
gestural reportage sketches. This system uses OpenAI vision models to read all three layers and
makes them searchable through natural language queries.

This repo is also being shaped for a public-sharing mode where the code and selected
derived artifacts can be published without redistributing the raw collection PDFs or the
live local vector store.

---

## Quick Start

```bash
# 1. Set up
cd topolski-explorer
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
# The local raw corpus should already be present in staged_data_raw/

# 2. Create the dedicated environment
python3 -m venv ~/venv4
source ~/venv4/bin/activate
pip install -r requirements.txt

# 3. Build the local working dataset and index
python pipeline/02_preprocess.py   # Normalize raw PDFs/metadata and render page images
python pipeline/03_transcribe.py   # GPT vision: transcribe text + describe sketches
python pipeline/04_embed_index.py  # Embed saved outputs and load the local Chroma index

# 4. Start the local search app
python pipeline/05_search.py
# Open http://localhost:5050
```

For a quick demo-sized run, set `MAX_ITEMS=10` in `.env` before running steps 2–4.
That lets you verify the local workflow before spending credits on the full corpus.

---

## Architecture

```
Raw local corpus
(`staged_data_raw/*.pdf`, `staged_data_raw/*.json`)
    |
    v
02_preprocess.py       Normalize metadata + render page images into `data/staged/`
    |
    v
03_transcribe.py       OpenAI vision (high detail) → per-page transcription JSON
    |                  Extracts: typeset text, handwritten text, sketch descriptions,
    |                  named entities (people/places/events/dates), page summary
    v
04_embed_index.py      OpenAI text-embedding-3-small → ChromaDB
    |                  Multiple retrieval lanes per page: text, sketch, entities,
    |                  summary, blended
    |
    v
05_search.py           Flask app
                       Query → embed → local Chroma retrieval
                       → page-level aggregation across chunk types
                       → optional reranking
                       → UI with page image + explanation + source evidence
```

---

## The Hard Problem

Standard OCR fails on Topolski's handwriting. The prototype (`pipeline/reference/`)
attempted Tesseract-based enrichment and region detection — useful for understanding
the data structure, but the handwritten content came back as garbage.

The current build uses a hybrid model strategy: stronger vision models for exacting rereads
and evaluation, faster models for broad-corpus throughput. That split turned out to matter
under real rate limits.

The durable artifact is local even though API models are used during processing:

- page images are stored locally
- transcription outputs are stored locally
- embeddings and the Chroma index are stored locally
- the search UI runs locally against those saved artifacts

Optional reranking can add explanations, but the core search path remains local.

---

## Collection Background

See `CONTEXT.md` for full background on Topolski, the Chronicle, and the research
questions this system is designed to answer.

## Public-Sharing Shape

The intended public version of this project is not:

- a redistribution of the source scans
- a checked-in live Chroma database
- a repo full of runtime-generated page images and crops

The intended public version is:

- code
- docs
- selected derived manifests
- a rebuild path for the local vector index from exported assessment JSON

See `PUBLISHING.md` for the exact split and the export workflow.

## Next Layers

Two follow-on tracks are now part of the project by default:

- a derived feature-manifest layer that records what each page and item appears to contain
- a local dashboard/status surface that shows processing coverage, indexed features, and corpus observability

These are not optional polish tasks. They are the next step toward making search results interpretable and trustworthy.

---

## Prior Work

`pipeline/reference/` contains the original DL-test-1 prototype scripts (May–June 2025).
They are preserved for reference and document the exploration arc that led here.
Do not run them — they use a different directory structure and outdated model choices.

Key decisions that changed from prototype to this build:
- EfficientNetB2 image embeddings → GPT-4o vision captioning + semantic text embeddings
- Tesseract OCR → GPT-4o vision HTR (handwriting transcription)
- Hardcoded Windows paths → env-configured, cross-platform
- Monolithic scripts → staged pipeline with resume safety
- remote collection download assumption → local raw corpus as the working source

## Derived Artifact Library

The project is now moving toward a more compelling public shape than "pipeline skeleton."

The live goal is:

- inspect the collection once
- make multiple kinds of assessment about each page and item
- save those assessments as durable structured outputs
- rebuild a local search index from those saved outputs
- use that index to find things back in the original source material

The first public-safe version of that layer now exists:

- `scripts/export_public_artifacts.py` copies selected manifests and builds a sanitized
  per-item assessment library under `published_artifacts/artifact_library/`
- the current exported snapshot contains a partial but real derived library from the live run
- `pipeline/12_embed_published_artifacts.py` is the rebuild path for indexing from those
  exported assessments without the raw PDFs

This is still partial because the current frozen snapshot covers `82` of the `138` local
items, but it is no longer just an idea.

---

## Project Structure

```
topolski-explorer/
├── .env.example             Config template
├── .gitignore
├── README.md                This file
├── CONTEXT.md               Collection background and research goals
├── AGENTS.md                Agent build briefs (hackathon use)
├── ROADMAP.md               Project roadmap and next work
├── PUBLISHING.md            Public-sharing notes and export policy
├── published_artifacts/     Intended home for shareable derived outputs
├── requirements.txt
├── scripts/
│   ├── export_public_artifacts.py
│   └── transcription_status.py
├── pipeline/
│   ├── 01_extract.py        Legacy collection downloader scaffold
│   ├── 02_preprocess.py     Raw corpus → normalized working dataset + page images
│   ├── 03_transcribe.py     OpenAI vision per page
│   ├── 04_embed_index.py    Embed + load ChromaDB
│   ├── 05_search.py         Flask search app
│   ├── 12_embed_published_artifacts.py
│   └── reference/           Original prototype scripts (DL-test-1, 2025)
├── staged_data_raw/         Local raw corpus of PDFs + metadata JSON
├── templates/
│   └── index.html           Search UI
└── data/                    GITIGNORED — live generated data lives here
    ├── staged/              Normalized metadata, page images, transcriptions
    └── chroma/              ChromaDB vector index
```

---

## Notes for Agents

- Read `AGENTS.md` for your specific brief before starting.
- Read `ROADMAP.md` for the current next-layer requirements.
- All config comes from `.env` via `python-dotenv`.
- Every pipeline script must be idempotent — check before doing work, skip completed items.
- Log using Python `logging`, not `print()`.
- Catch API errors and continue — do not crash on a single failed item.
- Use `tenacity` for retry logic on transient API failures.
- The collection is public — no credentials needed for download.
- The OpenAI API key is provided in `.env` — use it without hesitation.
- Treat the feature-manifest layer and dashboard/status surface as part of the expected build path, not as optional extras.
- If preparing the project for public sharing, use `scripts/export_public_artifacts.py`
  instead of moving files directly out of `data/` while background runs are active.
- The public-sharing direction is no longer hypothetical: exported assessment JSON should
  be treated as a first-class artifact layer, not just documentation garnish.
