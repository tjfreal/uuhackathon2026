# Decksmith

This directory is included here as one example build inside the larger `uuhackathon2026` submission. It is a promising workflow prototype, not a polished standalone product.

Decksmith is a local-first presentation generator for turning project notes, markdown plans, and structured slide specs into editable Keynote and PowerPoint decks.

The project exists because once a piece of work becomes worth sharing, presentation stops being a side task and becomes part of the build system. Decksmith packages that step without trying to automate away the judgment required to tell a story well.

## What It Is

- A reusable AppleScript-based deck renderer: [scripts/build_presentation_template.applescript](scripts/build_presentation_template.applescript)
- A simple slide-spec format that carries title, body, notes, and optional per-slide image attachment
- A package pattern for self-contained decks in [outputs](outputs)
- A working set of real example decks:
  - [outputs/hackathon-builds-overview](outputs/hackathon-builds-overview)
  - [outputs/throughline](outputs/throughline)
  - [outputs/julia-stl](outputs/julia-stl)

Decksmith is not a design system and not a hosted presentation app. It is a local authoring workflow for getting from project thinking to an editable deck quickly.

## How It Works

The current workflow is:

1. Write or collect source material in markdown.
2. Condense that into `slides.txt` using a delimiter-based slide format.
3. Set deck metadata in `deck_config.txt`.
4. Generate a package-local AppleScript from the shared template.
5. Run that script in macOS with Keynote installed.
6. Refine the resulting `.key` or `.pptx` file by hand.

The central idea is separation:

- deck content lives with the deck package
- rendering logic lives in the shared template
- generated decks remain editable artifacts, not final frozen exports

## Slide Format

The source row format is intentionally small:

```text
layout|||title|||body|||speaker notes|||image path|||image layout
```

Required fields:

- `layout`
- `title`
- `body`
- `speaker notes`

Optional fields:

- `image path`
- `image layout`

This keeps authoring lightweight while still carrying the most useful presentation intent.

### Example Rows

```text
Title|||Project Name|||Short thesis|||Speaker notes|||render.png|||full
Title & Bullets|||Tooling Breakthrough|||Fast tuning\nLocal preview|||Notes for the presenter|||screenshot.png|||sidebar-right
Title|||Image Study||||A note about this image-only slide.|||detail.png|||center
```

## Image Model

Images are attached intentionally per slide rather than gathered directory-wide.

`deck_config.txt` can define:

```text
image_root=/abs/path/to/project
```

Each slide may then add:

- `image path`
- `image layout`

Supported layouts:

- `full`
- `center`
- `sidebar-right`
- `sidebar-left`

When an image is attached, Decksmith appends metadata into the presenter notes:

- filename
- full path
- dimensions
- file size
- modified timestamp

## Repository Layout

```text
.
├── README.md
├── learnings.md
├── presentation.md
├── roadmap.md
├── scripts
│   └── build_presentation_template.applescript
└── outputs
    ├── README.md
    ├── hackathon-builds-overview
    ├── throughline
    └── julia-stl
```

## What The Example Packages Show

The current example decks prove that the pattern works across materially different presentations:

- `hackathon-builds-overview`: portfolio-level overview deck
- `throughline`: project-specific deck
- `julia-stl`: project deck with explicit image-attached slides

Each package includes source files and may also include generated `.key` and `.pptx` outputs as working artifacts.

## Running It

Decksmith currently targets macOS with Keynote installed.

To build a deck:

1. Duplicate an existing package under `outputs/` or create a new one.
2. Edit `deck_config.txt`, `slides.txt`, and `narrative_plan.md`.
3. Ensure `build_presentation.applescript` exists in that package.
4. Run the AppleScript to generate the `.key` and `.pptx` outputs.

The package-local README files document each example deck briefly.

## Related Notes

- Authoring reference: [AUTHORING.md](AUTHORING.md)
- Design lessons: [learnings.md](learnings.md)
- Public framing: [presentation.md](presentation.md)
- Next steps: [roadmap.md](roadmap.md)
