# Presentation

## One-Sentence Version

This project started as “turn a Julia set into an STL” and matured into “use Julia-set structure as a controlled deformation language for a printable vase.”

## Short Story Arc

The strongest presentation sequence is:

1. show the initial ambition
2. show why the literal fractal-to-mesh path failed
3. explain the reframing from silhouette to modulation
4. show the playground as the tuning instrument
5. show the render, print, and final STL package

## What The Audience Should Understand

- The artifact is a vase, not a pure mathematical model.
- The interesting technical move was interpretive, not just computational.
- The project succeeded because the workflow changed, not because the math got more extreme.

## Framing The Work

This is best presented as a small creative engineering project with a clear research arc:

- begin with image-based Julia experiments
- discover that raw contour extraction is structurally weak
- move to ordered ring sampling and direct meshing
- use interactive previews to navigate a narrow aesthetic space
- validate with a render and a physical print

## Key Evidence To Show

- Final render: [assets/images/render-blender.png](assets/images/render-blender.png)
- Physical print: [assets/images/print-photo.jpg](assets/images/print-photo.jpg)
- Playground screenshot: [assets/images/playground-screenshot.png](assets/images/playground-screenshot.png)
- Generator screenshot: [assets/images/generation-screenshot.png](assets/images/generation-screenshot.png)
- Canonical mesh: [assets/models/julia_vase.stl](assets/models/julia_vase.stl)
- Preview history: [assets/previews](assets/previews)

## The Real Technical Story

The audience does not need every script. They need the throughline:

- the early pipeline used raster images and contour extraction
- that produced noisy geometry and weak forms
- the project improved once the vase stayed mostly circular
- Julia structure became a modulation source instead of the literal outline
- one ordered ring per layer made watertight meshing straightforward
- the browser playground accelerated aesthetic judgment

## Why The Preview Files Matter

The preview series is not clutter if it is framed correctly. It shows that the project was tuned, not guessed.

Useful checkpoints:

- `v6`: first convincing concept
- `v9`: too aggressive, but informative
- `v11`: symmetry repair
- `v12` and `v13`: controlled refinements near the best region

## Recommended Slide Order

1. Title and one-sentence framing
2. Early failed approach: images, contours, point clouds
3. Reframe: Julia as modulation, not silhouette
4. Playground and preview iteration process
5. Final render
6. Physical print
7. What the generator now does
8. What remains to refine

## Closing Message

The strongest conclusion is not “I made a vase from a fractal.”

It is: “I found a repeatable way to turn a mathematically interesting signal into a tunable physical form, then packaged the process so other people can understand and reproduce it.”
