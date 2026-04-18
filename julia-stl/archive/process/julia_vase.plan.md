# Julia Vase Build Plan

## Goal
Build a standalone Python generator that produces a high-fidelity, watertight STL for a Julia-set-inspired vase form. The model should start as a circle, evolve through more complex cross-sections along Z, and resolve back to a circle at the top. The slicer will handle vase mode; the generated mesh should remain a conventional closed solid with flat top and bottom caps.

## Project Direction
This is a refinement of the existing repo, not a reinvention. Keep the current idea of evolving `c` values across layers, but replace the raster-image-to-contour pipeline with direct ordered ring generation so fidelity can scale cleanly for large prints.

## What To Keep
- The current “interesting in the middle, circular at both ends” shape intent.
- A layer-by-layer progression along Z.
- Existing Julia math as the source of each layer’s profile.
- A standalone workflow that lets output be judged without Blender in the loop.

## What To Replace
- Drop image-first perimeter extraction (`PIL` + `OpenCV` + contour recovery) as the primary geometry path.
- Drop point-cloud `.ply` output as the main artifact.
- Stop treating unordered boundary pixels as mesh input.

## Proposed Output Script
Create `julia_vase.py` as the single main entry point.

Core stages:
1. Define top-level parameters.
2. Compute the layer progression in `c`.
3. Sample one ordered closed ring per layer.
4. Blend early and late layers toward circles.
5. Smooth ring-to-ring noise without losing the overall silhouette.
6. Build a watertight triangle mesh with flat caps.
7. Scale to physical dimensions and export STL.
8. Print validation stats.

## Top-Level Controls
Expose these as easy sliders at the top of the script:

- `num_layers`: vertical resolution, default 240-320.
- `num_angles`: ring resolution, default 512-1024.
- `max_iter`: Julia iteration depth.
- `boundary_refine_steps`: precision vs. speed.
- `vase_height_mm`
- `vase_diameter_mm`
- `smoothing_iters`
- `start_circle_blend_layers`
- `end_circle_blend_layers`
- `output_path`

These are the main quality/performance levers for scaling to very large prints.

## Geometry Strategy
Represent the vase as a stack of rings, each with the same number of ordered vertices.

Per-layer workflow:
1. Compute `t` in `[0, 1]` from the layer index.
2. Compute `c(t)` using the existing progression idea, updated as needed after visual review.
3. For each angle, compute a radius for that layer.
4. Convert radii to XY coordinates in consistent winding order.
5. Apply optional in-ring smoothing in XY only.

Two acceptable implementations for radius sampling:

- Preferred: direct polar boundary search with binary refinement.
  This is slower, but gives a clean, ordered ring and scales well in fidelity.
- Fallback: image-based sampling only if direct sampling proves too slow.
  If used, it must still resample the contour into a fixed-count ordered ring before meshing.

The preferred path should be built first, with resolution controls exposed so speed can be tuned.

## Circle Transition Rules
The first and last layers should be explicitly blended toward circles so the vase starts and ends cleanly.

Approach:
- Define a blend envelope near the bottom and top.
- Interpolate between the sampled Julia radius profile and a perfect circle radius.
- Keep this blend smooth to avoid visible shoulders or pinch artifacts.

## Mesh Construction
Mesh generation should be deterministic and topology-stable:

- Connect adjacent rings using quads split into two triangles.
- Use a constant vertex count per ring.
- Add a bottom center vertex and a top center vertex.
- Cap both ends with triangle fans.
- Maintain consistent outward winding.

The mesh must export as binary STL.

## Validation
Each run should report:

- layer count
- angles per layer
- total vertices
- total faces
- bounding box in mm
- watertight status

If `trimesh` is available, check:
- `is_watertight`
- winding/normals consistency

## Milestones
1. Create `julia_vase.py` scaffold with parameters and mesh export.
2. Implement ring generation using direct boundary sampling.
3. Add circular blending at the bottom and top.
4. Build watertight sidewalls and caps.
5. Add smoothing controls and physical scaling.
6. Generate low-resolution preview STL quickly.
7. Generate high-resolution output for print evaluation.

## Risks And Mitigations
- Direct boundary sampling may be slow.
  Mitigation: keep `num_layers`, `num_angles`, and `boundary_refine_steps` as explicit sliders.
- High detail may create ugly high-frequency noise.
  Mitigation: add controlled smoothing and optional layer-to-layer radius damping.
- Some `c` paths may generate shapes that are mathematically interesting but visually poor.
  Mitigation: treat the `c` path as a tunable artistic control after the first watertight pipeline works.

## Definition Of Done
The first successful implementation should:

- run from the repository root with `python3 julia_vase.py`
- generate a watertight STL
- produce a vase-shaped solid with flat top and bottom
- begin circular, become visually interesting in the middle, and return to circular
- expose resolution controls that can be increased for large prints without changing code structure

## Immediate Build Order
Build the direct ring-based standalone generator first. Do not spend more time refining the current contour-recovery scripts unless they become useful as a temporary visual reference.
