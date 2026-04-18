# Learnings

## Core Reframe

- The project became stronger once it stopped trying to be a literal Julia-set solid.
- The useful interpretation is: keep a vase legible as a vase, then let Julia structure modulate the section.
- That makes this a design-and-parameter problem, not just a math-to-mesh conversion problem.

## What The Cleanup Clarified

- The repository is easier to understand when the final generator and the exploratory record are separated.
- The main story only needs two top-level tools:
  - [julia_vase.py](julia_vase.py) for STL export
  - [julia_vase_playground.html](julia_vase_playground.html) for rapid shape tuning
- Everything else is supporting history and belongs in [archive](archive).

## What Failed

- Raster-first workflows (`PIL` -> threshold -> contour recovery) lost too much structure and produced noisy boundaries.
- Revolve and height-map approaches made geometry quickly, but not geometry that felt like the right object.
- Strong shoulder and taper logic looked imposed rather than discovered.
- Full-loop `c` progressions introduced asymmetry that made the upper half feel unrelated to the lower half.
- Early deformation onset made the vase lose its body before it had established one.

## What Worked

- A direct ring-based mesh pipeline is the right architecture:
  - one ordered ring per layer
  - fixed point count per ring
  - deterministic ring-to-ring meshing
  - capped top and bottom for a watertight solid
- Symmetric progression matters more than raw fractal complexity.
- The best versions keep the outer envelope relatively stable and let the detail express itself through inward pulls and controlled modulation.

## Useful Artifact Insight

- [assets/point-clouds/stacked_julia_set2.ply](assets/point-clouds/stacked_julia_set2.ply) was one of the most informative intermediate outputs.
- It showed that the attractive forms were not coming from drift or wild flaring.
- The better shape language came from a stable body with stronger inward carving than outward expansion.

## Parameter Learning

- The good region is narrow.
- Small changes in `modulation_peak`, `detail_strength`, `c` scaling, or inward/outward weighting move the object quickly from elegant to bland or chaotic.
- The most reliable pattern so far is:
  - delayed detail onset
  - symmetric rise and return
  - inward-biased deformation
  - a mostly stable silhouette

## Preview Series Learning

- The preview STL series in [assets/previews](assets/previews) is worth keeping because it captures the actual search:
  - `v6` was the first clearly promising concept
  - `v9` established the upper bound by going too far
  - `v11` fixed the structural symmetry problem
  - `v12` and `v13` narrowed in on the current useful region

## Tooling Learning

- The browser playground was as important as the generator.
- [julia_vase_playground.html](julia_vase_playground.html) made it possible to tune language and proportion quickly instead of waiting on full STL exports.
- Shared logic between the playground and [julia_vase.py](julia_vase.py) turned exploration from blind iteration into guided refinement.

## Evaluation Learning

- The render in [assets/images/render-blender.png](assets/images/render-blender.png) proved the object is already visually credible.
- The print photo in [assets/images/print-photo.jpg](assets/images/print-photo.jpg) proved the form survives translation into a physical object.
- Those two artifacts changed the project from “promising experiment” to “shareable work with a clear next phase.”

## Best Current Mental Model

- Start from a circular vessel.
- Let Julia structure modulate it, not replace it.
- Delay the deformation.
- Preserve top-to-bottom symmetry.
- Favor inward carving over outward swelling.
- Lock the shape language before spending much more compute on fidelity.

## Next Refinement Frontier

- Concept refinement:
  - smoother, more wave-like undulation
  - fewer trench-like cuts
  - stronger continuity in surface flow
- Fidelity refinement:
  - higher layer and angle counts
  - higher scan/refine depth
  - comparison of whether smoother meshes improve the idea or merely expose it
