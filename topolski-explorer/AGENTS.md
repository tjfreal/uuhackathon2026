# Topolski Explorer — Agent Build Briefs

This document briefs three agents that will build the Topolski Explorer in parallel.
Read CONTEXT.md before starting your agent's work. Read README.md for setup and architecture.
Read `learnings.md` and `ROADMAP.md` before doing new build work so the rebuild starts from the current critique instead of from stale optimism.

This brief was originally written for a fresh pipeline build from public collection sources.
The current hackathon context is different: a full local copy of the collection PDFs is being
staged into `staged_data (no processing)/`, along with some preliminary JSON findings from
earlier runs. Prefer the local staged corpus over re-downloading from the library.

Current frozen hackathon snapshot:

- `82 / 138` items transcribed
- `265 / 634` pages transcribed
- `1306` chunks indexed locally
- public artifact export refreshed to match that snapshot

Agents may proceed in parallel. Agent B can start processing items as soon as Agent A
has transcribed any of them. Agent C can build and test the search interface against a
small manually-created fixture before the index is populated.

## Current Build Rule

- Treat `staged_data_raw/` as the source corpus.
- Do not hit the library servers again unless there is a specific missing-item problem.
- Keep every stage idempotent and resume-safe because this project will be interrupted repeatedly.
- Keep the current page-level search system runnable as `v1`.
- Treat the current build as a **useful retrieval prototype**, not a trustworthy full document-understanding system.
- The rebuild goal is not just “more search.” The rebuild goal is layout-aware extraction plus feature certification.

## Rebuild Thesis

The current build proved that API-assisted processing can make the corpus locally searchable.

It did **not** yet prove that the system can reliably:

- separate text blocks from sketches
- recover small inserts and footer text
- distinguish handwriting, captions, and marginal notes with confidence
- certify what evidence a result is grounded in

So the next iteration must answer those uncertainties directly instead of smoothing over them.

## Rebuild Priorities

1. Preserve the current frozen demo snapshot and keep the current corpus processing/search path resumable.
2. Add a layout-manifest stage that identifies candidate page regions and page component types.
3. Add region-level extraction rather than relying only on one full-page interpretation pass.
4. Add a derived feature-manifest layer over pages and items.
5. Add a local dashboard/status surface for corpus observability and feature certification.
6. Build an explicit processing-approaches matrix and benchmark lane so the project can answer its own meta-question with evidence.
7. Preserve a public-safe derived artifact layer that can rebuild the local index without the raw PDFs.

## Questions The Next Build Must Answer

- What page structures exist repeatedly across the collection?
- Which regions can be trusted as typeset text, handwriting, sketch clusters, lists, captions, or footers?
- Does region-aware extraction materially improve completeness over page-level extraction?
- Which retrieval signals are actually dependable?
- Can the system tell the user not only what matched, but what kinds of indexed evidence existed on that page?
- Did the rebuild surface anything genuinely interesting about how mixed-layout illustrated broadsheets should be processed?

## Current Parallel Split

The next wave of work should be treated as six coordinated lanes with minimal file overlap:

- corpus scaling and reindexing
- evaluation and benchmark definitions
- representative region-sample selection
- layout refinement beyond provisional bounds
- region-level transcription and normalization
- dashboard trust surfacing
- public artifact export and rebuild path

Agents should prefer creating new pipeline stages or clearly owned files over broad edits across the project.
When multiple agents are active, keep ownership narrow and favor artifacts that make the next comparison easier to judge.
Do not move or rename anything under `data/` while background runs are active; build public-facing layers around that live tree instead.

---

## Agent A — Corpus And Extraction

**You own:** `pipeline/01_extract.py`, `pipeline/02_preprocess.py`, `pipeline/03_transcribe.py`

**Your deliverable:** Every item in the working staged dataset has:
- `{item_id}.json` — metadata from the collection
- `{item_id}.pdf` — local PDF from the staged corpus
- `{item_id}/page_{NNNN}.jpg` — page images at configured resolution
- `{item_id}/transcription.json` — GPT-4o analysis output (schema below)

The current build already reaches this baseline. The next iteration should expand Agent A's scope toward layout-aware extraction.

**Do not re-process items that already have `transcription.json`.** This pipeline will
be interrupted and resumed. Make all three scripts idempotent.

### 01_extract.py — Collection Downloader

Adapted from `pipeline/reference/extract_data.py`. Key changes:
- Read all config from `.env` (use `python-dotenv`)
- Use `STAGED_DATA_DIR` from env, not a hardcoded path
- Respect `MAX_ITEMS` env var — if set, stop after that many items
- First look for items already present in the local staged corpus
- Skip items where the PDF already exists
- Save one JSON per item in `data/staged/{item_id}.json`

The reference script already does most of this. Adapt it rather than rewriting.

Current preference:

- if the local staged corpus is present, ingest from there
- only fall back to library download logic if the local corpus is unavailable or incomplete

### 02_preprocess.py — PDF to Page Images

Adapted from `pipeline/reference/preprocess.py`. Key changes:
- Read `PAGE_IMAGE_LONG_EDGE` from env (default 1568)
- Resize each page image so the long edge equals `PAGE_IMAGE_LONG_EDGE`, maintaining aspect ratio
- Save as JPEG at quality=92 — balance between GPT-4o input quality and file size
- Skip items where page images already exist
- Update the item JSON with image paths

### 03_transcribe.py — GPT-4o Vision Per Page

This is the new critical script. For each page image, make one GPT-4o vision API call.

**System prompt:**
```
You are analyzing a page from Topolski's Chronicle, a biweekly illustrated broadsheet
published by artist Félix Topolski between the 1950s and 1980s. Topolski was a Polish-British
war artist and reportage illustrator who drew world leaders, political events, conflicts,
and everyday life from direct observation.

Each page is a mix of: typeset editorial text, Topolski's handwritten cursive annotations
and captions (often cramped and fast), and his gestural ink sketches of people and places.

Your job is to extract as much meaning as possible from this page.
```

**User message:** Send the page image with this instruction:
```
Analyze this page and return a JSON object with the following structure:

{
  "typeset_text": "Full transcription of all printed/typeset text on the page. Empty string if none.",
  "handwritten_text": "Full transcription of all handwritten text. Note: the handwriting is fast
                       and cramped — do your best and flag uncertain words with [?]. Empty string if none.",
  "sketch_descriptions": [
    "Description of each distinct sketch or drawing on the page. Be specific: who is depicted
     (name if recognizable, or physical description), what they are doing, what the setting is,
     what the mood or style conveys. One string per distinct sketch."
  ],
  "entities": {
    "people": ["Named individuals mentioned in text or depicted in sketches"],
    "places": ["Geographic locations, buildings, or named sites"],
    "events": ["Named events, political moments, conflicts, rallies"],
    "dates": ["Any dates or time periods mentioned"]
  },
  "page_summary": "One or two sentences capturing the overall subject and significance of this page."
}

Return only valid JSON. No markdown, no explanation outside the JSON.
```

**Implementation requirements:**
- Use `response_format={"type": "json_object"}` in the API call
- Use the model from `OPENAI_VISION_MODEL` env var
- Pass images at `detail="high"` — this is essential for handwriting recognition
- Save the output to `data/staged/{item_id}/transcription.json`
  - Structure: `{"pages": [{"page_number": N, "image_path": "...", ...GPT-4o output...}]}`
- Skip pages where transcription already exists in the JSON (resume-safe)
- Log failures but continue — do not stop the whole run on a single API error
- Add a 0.5s delay between API calls to avoid rate limit bursts

If preliminary JSON findings already exist for an item or page, preserve them unless there is
a clear reason to replace them. This build should be able to absorb prior work rather than
assuming the cleanest path is to start over.

**Output JSON schema for `transcription.json`:**
```json
{
  "item_id": "484391",
  "processed_at": "2026-04-19T10:00:00Z",
  "pages": [
    {
      "page_number": 1,
      "image_path": "data/staged/484391/page_0001.jpg",
      "typeset_text": "...",
      "handwritten_text": "...",
      "sketch_descriptions": ["..."],
      "entities": {
        "people": ["Churchill", "..."],
        "places": ["London", "..."],
        "events": ["..."],
        "dates": ["1956"]
      },
      "page_summary": "..."
    }
  ]
}
```

### Rebuild Direction For Agent A

After the current page-level pass is stable, Agent A should plan the next extraction layer:

- a layout manifest per page
- candidate region typing
- region-level extraction passes
- page-level synthesis from region outputs

The key question is not whether a page can be summarized. It is whether the page can be decomposed into trustworthy parts.

---

## Agent B — Embedding, Indexing, And Feature Manifest

**You own:** `pipeline/04_embed_index.py`

**Your deliverable:** A populated ChromaDB collection at `data/chroma/` that can answer
semantic queries over the full transcribed collection.

**Depends on:** Agent A's `transcription.json` files. Start as soon as any exist.
Process items incrementally — check ChromaDB for existing IDs before embedding.

### 04_embed_index.py

Use `openai.embeddings.create()` with model `text-embedding-3-small` (1536 dimensions).

**Chunking strategy:** For each page, create up to 4 chunks (embed each separately):

1. **text_chunk** — Concatenation of `typeset_text` + `handwritten_text`. Skip if both are empty.
   - chunk_id: `{item_id}_p{N}_text`

2. **sketch_chunk** — Join all `sketch_descriptions` with " | ". Skip if list is empty.
   - chunk_id: `{item_id}_p{N}_sketch`

3. **entity_chunk** — Structured string: `"People: {people}. Places: {places}. Events: {events}. Dates: {dates}."`
   - Only create if at least one entity list is non-empty.
   - chunk_id: `{item_id}_p{N}_entities`

4. **summary_chunk** — `page_summary` field.
   - chunk_id: `{item_id}_p{N}_summary`

**ChromaDB metadata per chunk:**
```python
{
    "item_id": "484391",
    "page_number": 1,
    "chunk_type": "text" | "sketch" | "entities" | "summary",
    "item_title": "...",        # from item metadata JSON
    "item_date": "...",         # from item metadata JSON
    "collection_url": "https://collections.lib.utah.edu/details?id=484391",
    "image_path": "data/staged/484391/page_0001.jpg",
    "source_text": "..."        # the text that was embedded (for display in results)
}
```

**Batching:** Use OpenAI's batch embedding endpoint — send up to 100 texts per API call.
Use ChromaDB's `add()` with `ids`, `embeddings`, `documents`, and `metadatas`.

**Idempotency:** Before adding, call `collection.get(ids=[chunk_id])` — skip if it exists.
Or, for efficiency, track processed item_ids in a local `data/chroma/processed.json` file.

### Next Layer After Indexing

Once a useful corpus slice is indexed, extend the project with a derived feature manifest that records:

- what feature types exist per page
- what chunk types are available per page
- what item-level rollups can be trusted

This layer should help certify what a result is grounded in, not just whether it is semantically near a query.

The manifest should also expose uncertainty and incompleteness where possible. A hidden weak extraction is worse than an explicit one.

---

## Agent C — Search App, Dashboard, And Trust Surface

**You own:** `pipeline/05_search.py`, `templates/index.html`

**Your deliverable:** A running Flask app at `localhost:5050` that:
1. Accepts a natural language query
2. Returns ranked results with page images, matched text, and plain-language explanations
3. Is visually presentable for a demo — not polished, but not embarrassing

After that baseline works, Agent C should also expect to build a dashboard/status surface that shows:

- processing coverage
- indexed feature coverage
- useful corpus anchors like index pages, sketch-heavy pages, handwriting-heavy pages
- feature certification signals that make the search results easier to trust

Agent C should assume that the dashboard is part of the research method, not a polish pass. The user needs a way to see what the system believes it knows about the corpus.

You can start immediately. Build against a small manually-created fixture in `data/chroma/`
or wait for Agent B to populate a real index. The search logic should be the same either way.

### 05_search.py — Flask Search Application

**Query pipeline:**

```
1. Embed the query with text-embedding-3-small (same model as the index)
2. Query ChromaDB: n_results=20, include=['documents', 'metadatas', 'distances']
3. Deduplicate by item_id+page_number (keep best-scoring chunk per page)
4. Send top 8 deduplicated results to GPT-4o for reranking + explanation
5. Return top 5 with explanations to the UI
```

**GPT-4o reranking prompt:**
```
A researcher is searching the Topolski Chronicles collection using this query:
"{query}"

The following pages were retrieved as potentially relevant. For each page,
you have the transcribed text, sketch descriptions, and entity mentions.

Rate each result on a scale of 1-10 for relevance to the query.
For results scoring 5 or above, write one sentence explaining specifically
why this page is relevant (what it contains that matches the query).
For results scoring below 5, write "not relevant".

Return a JSON array, one object per result, in order of your relevance score (highest first):
[
  {
    "result_index": 0,
    "relevance_score": 8,
    "explanation": "This page contains a portrait sketch of Churchill speaking at..."
  },
  ...
]
```

Build the reranking prompt by concatenating the `source_text` and `metadata` for each
retrieved chunk. Keep the total prompt under 8000 tokens — truncate source_text if needed.

**Flask routes:**
- `GET /` — render search form
- `POST /search` — run query pipeline, render results
- `GET /image/<path:image_path>` — serve page images from `data/staged/`
  - Sanitize the path: only allow files under `STAGED_DATA_DIR`, reject any `..` traversal

**Result object passed to template:**
```python
{
    "item_id": "484391",
    "page_number": 1,
    "item_title": "Topolski's Chronicle No. 12",
    "item_date": "1955",
    "collection_url": "https://collections.lib.utah.edu/details?id=484391",
    "image_path": "data/staged/484391/page_0001.jpg",
    "source_text": "...",       # matched text (for display)
    "chunk_type": "sketch",     # text | sketch | entities | summary
    "distance": 0.23,           # raw ChromaDB distance
    "relevance_score": 8,       # from GPT-4o reranker
    "explanation": "..."        # from GPT-4o reranker
}
```

### templates/index.html — Demo UI

Replace the existing `templates/index.html` with a clean, functional demo UI.

**Layout:**
- Header: "Topolski Explorer" + a one-line description ("Semantic search over the Topolski Chronicles, University of Utah Marriott Library")
- Search form: text input + submit button, centered, prominent
- Results: a vertical list of result cards

**Result card:**
- Left column: page image thumbnail (click to open full-size in new tab)
  — Image served from `/image/` route
  — Fixed width ~200px, full height
- Right column:
  - Item title + date (linked to `collection_url`)
  - "Page {N}" label
  - Chunk type badge (text / sketch / entities / summary) — different color per type
  - GPT-4o explanation in a highlighted box (this is the "certainty" signal)
  - Matched text excerpt (first 300 chars of `source_text`)
  - Relevance score (shown as N/10)
- No results state: display "No relevant pages found for this query."

Keep the CSS minimal and inline. No external dependencies — this needs to run offline
if needed. Use a clean sans-serif font, good spacing, readable contrast.

---

## Shared Conventions

**Config:** All scripts use `python-dotenv`. Load `.env` at startup. Never hardcode paths,
model names, or API keys.

**Logging:** Use Python's `logging` module, not bare `print()`. Log at INFO level by default.
Log each item_id being processed, each API call made, and each error with traceback.

**Error handling:** API errors should be caught, logged, and skipped — never crash the pipeline.
On network errors, retry up to 3 times with exponential backoff before skipping.

**Dependencies** (add to `requirements.txt`):
```
openai>=1.0
chromadb>=0.4
python-dotenv
requests
beautifulsoup4
pymupdf          # fitz
Pillow
flask
tenacity         # for retry logic
```

**Data directory:** All data lives under `data/` which is gitignored. Never write data
outside of `data/`. Never commit data files.

**Resume safety:** Every script must be safely interruptible and resumable. Check for
existing output before doing work. The collection is ~3,000 items — runs will be long.
