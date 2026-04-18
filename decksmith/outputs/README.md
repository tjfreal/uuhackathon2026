# Output Packages

This directory holds self-contained Decksmith deck packages.

Each package includes:

- `deck_config.txt`
- `slides.txt`
- `narrative_plan.md`
- `build_presentation.applescript`

Generated `.key` and `.pptx` files may also appear beside those sources after a build. They are useful working artifacts, but the source files are the real source of truth.

Current example packages:

- `hackathon-builds-overview`
- `throughline`
- `julia-stl`

To create a new deck, duplicate one package, update the config and slide source, then run the package-local AppleScript on a Mac with Keynote installed.
