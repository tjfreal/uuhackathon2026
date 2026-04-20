# Topolski Eval Kit

This directory holds the smallest useful evaluation layer for the rebuild.

The point is not leaderboard theater. The point is to compare retrieval and extraction
approaches against a stable set of questions and pages so the project can answer its
own meta-question with evidence.

## Files

- `benchmark_queries.json`
  A starter query set covering named people, places, events, visual scenes, list/index pages,
  and mixed-layout retrieval.
- `judgment_template.json`
  A schema for recording what each approach surfaced, what was actually useful, and where trust broke down.

## Usage

1. Keep `v1` search runnable as the baseline.
2. Build a representative page subset with:
   `python pipeline/11_select_region_eval_sample.py`
3. Run retrieval checks and region-aware experiments against that subset.
4. Record judgments in a copy of `judgment_template.json`.

## What To Look For

- Does the approach surface the right item or page neighborhood?
- Does the result expose enough evidence to trust why it matched?
- Do region-aware passes recover information the whole-page pass missed?
- Do index pages, footers, sidebars, and handwriting-heavy pages behave differently?
- Are we learning something general about this document class, or just stacking complexity?
