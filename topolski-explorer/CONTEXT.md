# Topolski Explorer — Collection Context

## Who Was Félix Topolski

Félix Topolski (1907–1989) was a Polish-British artist and war correspondent. He was present at major events of the 20th century and recorded them through drawing — fast, gestural, ink-heavy reportage sketches. He was a draftsman first and a journalist second. He knew Churchill, Malcolm X, the Pope, and a long list of world figures, and drew them all from life.

He is not well known outside art history circles, which is part of what makes the collection worth surfacing.

## The Chronicle

From the 1950s through the 1980s, Topolski self-published *Topolski's Chronicle* — a biweekly broadsheet-format illustrated publication, produced nearly continuously for 25 years. The Marriott Library at the University of Utah holds a nearly complete run: approximately 3,000 items (issues/pages).

Each issue is a mix of:
- **Typeset text blocks** — editorial prose, captions, bylines
- **Topolski's handwritten annotations and captions** — his distinctive, fast, often-cramped cursive interspersed with drawings
- **Gestural sketches** — reportage drawings of people, crowds, places, and events; varying from loose gesture drawings to detailed portrait work

The handwriting is genuinely difficult. It is not careful penmanship. Standard OCR fails on it. This is the central technical challenge of the project.

## The Collection Online

The collection is publicly accessible. No authentication required.

- Collection search: `https://collections.lib.utah.edu/search?facet_setname_s=uum_tc`
- Item detail page: `https://collections.lib.utah.edu/details?id={ITEM_ID}`
- Each item has a downloadable PDF and structured metadata (title, date, creator, description, subject tags)

The pipeline scripts handle collection traversal and download automatically.

## What Researchers Want to Find

These search goals were defined by Luke (art history faculty, domain expert on the collection):

- **Political figures** — who appears in a given issue, especially named world leaders
- **National events and rallies** — issues tied to specific political moments
- **War and conflict** — combat reporting, protest imagery, military subjects
- **Geographic regions** — did Topolski visit and draw a specific place?
- **Vanished places** — locations that no longer exist due to war, disaster, climate, or development
- **Topolski's process** — issues that reveal how he worked, his method, his perspective
- **Architectural subjects** — buildings, cityscapes, monuments

The core query pattern is: *"Was Topolski there? Did he draw it? What did he make of it?"*

The system needs to return answers the researcher can trust — not just ranked similarity scores, but results with enough evidence (page image, transcription, explanation) to verify or dismiss.

## Prior Work (DL-test-1)

A prototype pipeline was built in 2025 and is preserved in `pipeline/reference/`. Key findings:

- Collection download and PDF extraction work well (`extract_data.py`, `preprocess.py`)
- Metadata-based vectorization is weak — metadata is inconsistent and duplicated across the collection
- OCR-based vectorization is far more promising but was not completed
- Standard Tesseract OCR cannot handle the handwritten content
- Image region extraction ran for days and produced very granular clippings — the filtering heuristics need refinement
- The search app (`search_app.py`) uses Flask + ChromaDB + EfficientNetB2 — this architecture is sound; the model choices are being upgraded

## What This Build Is

A hackathon project targeting a demoable semantic search system over the Topolski Chronicles. The key upgrade from the prototype is replacing local OCR and image models with GPT-4o vision for page understanding — which handles handwriting, sketch description, and entity extraction in a single pass per page.

Target demo: a researcher types a query ("Churchill at a rally", "war aftermath sketches", "places that may no longer exist") and gets back page-level results with the source image, the transcribed/described content, and a plain-language explanation of why the result is relevant.
