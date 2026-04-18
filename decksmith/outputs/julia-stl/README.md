# Julia STL Deck

This is a Decksmith output package for the `julia-stl` project.

## Files

- `deck_config.txt`: output metadata and source references
- `slides.txt`: slide content and speaker notes
- `narrative_plan.md`: talk framing
- `build_presentation.applescript`: project-specific renderer generated from the Decksmith template

## Build

The included `build_presentation.applescript` is a sanitized example and may need its `outputDir` reset locally before use.

Run it on a Mac with Keynote installed to generate:
- `julia-stl.key`
- `julia-stl.pptx`
