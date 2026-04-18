# Authoring Guide

This file describes the current Decksmith authoring model: what belongs in a deck package, how `deck_config.txt` works, and how to write `slides.txt`.

## Deck Package Shape

Each deck package under `outputs/` should contain:

- `deck_config.txt`
- `slides.txt`
- `narrative_plan.md`
- `build_presentation.applescript`
- optional generated outputs: `.key` and `.pptx`

The source files are the source of truth. Generated deck binaries are working artifacts.

## `deck_config.txt`

Decksmith reads simple `key=value` lines.

Current supported keys:

- `deck_name`
  - output filename stem for `.key` and `.pptx`
- `theme`
  - Keynote theme name
- `width`
  - deck width in pixels
- `height`
  - deck height in pixels
- `slides_file`
  - slide source filename, usually `slides.txt`
- `image_root`
  - optional root directory for relative image paths

### Example

```text
deck_name=julia-stl
theme=Bold Color
width=1920
height=1080
slides_file=slides.txt
image_root=../julia-stl/assets/images
```

## `slides.txt`

Each non-empty, non-comment line is one slide:

```text
layout|||title|||body|||speaker notes|||image path|||image layout
```

The delimiter is `|||`.

Required fields:

1. `layout`
2. `title`
3. `body`
4. `speaker notes`

Optional fields:

5. `image path`
6. `image layout`

If a line has only the first four fields, it is still valid.

Lines beginning with `#` are ignored.

## Escapes

Decksmith currently decodes:

- `\n` as a newline
- `\t` as a tab

That is mainly useful for bullet-like body text and multiline notes inside one row.

## Layout Names

Decksmith passes the `layout` field directly to Keynote as a master slide layout name. That means the name must exist in the selected Keynote theme.

Common examples:

- `Title`
- `Title & Bullets`
- `Title - Center`

If the chosen theme does not have the named layout, the deck may not build correctly.

## Image Paths

The `image path` field can be:

- an absolute path
- a relative path resolved from `image_root`

If `image_root` is empty, Decksmith uses the path as written.

## Image Layouts

Supported image layout values:

- `full`
- `center`
- `sidebar-right`
- `sidebar-left`

If the image layout is omitted but an image path is present, Decksmith defaults to `center`.

## Example Slide Rows

```text
Title|||Decksmith|||Local-first deck generation|||Opening thesis and setup
Title & Bullets|||Why It Exists|||Presentation is part of the work\nEditable outputs matter|||Explain why automation stops short of final design
Title|||Julia STL Deck||||Use this slide to show the render|||render-blender.png|||full
Title & Bullets|||Tooling Breakthrough|||Per-slide images\nPackage-local builds\nSpeaker notes preserved|||Call out the current strengths|||playground-screenshot.png|||sidebar-right
```

## Authoring Tips

- Keep slide titles short.
- Treat `narrative_plan.md` as the longer thinking space and `slides.txt` as the compiled version.
- Use package-local README files only for package-specific notes, not for general tool documentation.
- Start from an existing package when testing a new talk.
- Only add images where they materially help the narrative.

## Current Limits

- Decksmith is macOS-only for now because it depends on Keynote AppleScript.
- The format supports one optional image per slide.
- The layout vocabulary for images is intentionally small.
- Theme compatibility depends on the layout names available in that Keynote theme.
