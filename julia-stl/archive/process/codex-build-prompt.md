# Julia Set Vase — Codex Build Prompt

## Goal

Write a single, self-contained Python script (`julia_vase.py`) that generates a high-fidelity, watertight STL file of a Julia set vase suitable for 3D printing. No Blender dependency — pure Python with numpy, scipy (optional), and numpy-stl or trimesh for STL export.

The output should be print-ready at ~80mm tall, ~60mm diameter, with smooth continuous surfaces that reward vase-mode printing (1 perimeter, no top/bottom layers). The shape should be visually compelling: evolving Julia set cross-sections that start small, open wide at the waist, and close again at the top.

---

## Background: What Has Been Built

This is an active project with ~13 iterations. Here is what we know works and what has failed.

### Working approach (juliagen_13_claude.py — Blender internal script)

The best boundary detection uses **polar ray + binary bisection search**:

```python
def find_boundary_radius(theta, c):
    direction = cmath.exp(1j * theta)
    if julia_iter_count(0, c) < MAX_ITER:
        return None  # Disconnected Julia set
    scan_steps = 100
    r_inner = 0.0
    for i in range(1, scan_steps + 1):
        r = (i / scan_steps) * R_MAX
        z = r * direction
        if julia_iter_count(z, c) == MAX_ITER:
            r_inner = r
        else:
            r_lo, r_hi = r_inner, r
            for _ in range(BISECT_STEPS):
                r_mid = (r_lo + r_hi) / 2
                z_mid = r_mid * direction
                if julia_iter_count(z_mid, c) == MAX_ITER:
                    r_lo = r_mid
                else:
                    r_hi = r_mid
            return (r_lo + r_hi) / 2
    return R_MAX
```

This is the right approach — it finds the filled Julia set boundary precisely. Do not use grid sampling + contour extraction (earlier approach using PIL + OpenCV): it produces noisy, non-manifold point clouds that can't be meshed cleanly.

### Working c-path

The c-path traces a teardrop inside the Mandelbrot set, so all Julia sets along the path are **connected** (filled, with no fractures). The path starts and ends at c=0 (circle), opens through interesting territory, and closes again:

```python
def compute_c(t):
    """t in [0, 1] → complex c value on teardrop path inside Mandelbrot set."""
    theta = 2 * math.pi * t
    radius = 0.7885 * (1 - abs(2 * t - 1))
    return radius * cmath.exp(1j * theta)
```

This was confirmed across juliagen09a through juliagen13. The radius coefficient 0.7885 keeps c just inside the Mandelbrot boundary for all t. The teardrop envelope `(1 - abs(2*t-1))` makes the radius swell to max at t=0.5 and collapse to 0 at t=0 and t=1.

### Known failure modes

1. **Disconnected Julia sets** — if c steps outside the Mandelbrot boundary, the Julia set becomes a Cantor dust. `find_boundary_radius` returns None for those layers. Guard against this; skip or interpolate affected layers.

2. **Non-manifold mesh** — the Blender mesh script built quads between rings but occasionally produced non-manifold edges near the top/bottom caps. Fix: use a fan triangulation for caps (center vertex → each edge of the ring), and ensure ring vertex count is constant across all layers.

3. **Rough surface** — grid sampling produces jagged rings. Polar ray tracing fixes this, but high NUM_ANGLES (≥512) is needed for print-quality smoothness. Also: apply one pass of **ring-level Laplacian smoothing** before meshing — average each vertex with its two neighbors in the ring, 2–3 iterations.

4. **STL not watertight** — caused by either: (a) open top/bottom, (b) non-manifold edges, (c) degenerate quads from radius=0 at poles. Fix: always cap top and bottom with fan triangles from a computed centroid.

---

## Specification

### Script: `julia_vase.py`

**Dependencies** (all pip-installable, no Blender):
- `numpy`
- `numpy-stl` (`pip install numpy-stl`) OR `trimesh` — prefer trimesh for its watertight checking
- `scipy` — optional, for Laplacian smoothing

**Parameters** (at top of script, easy to tune):
```python
NUM_ANGLES   = 512    # Points per ring — higher = smoother silhouette
NUM_LAYERS   = 200    # Z-layers — higher = smoother vertical transitions
MAX_ITER     = 256    # Iteration depth — higher = sharper boundary
ESCAPE_RADIUS = 2.0  # Standard escape radius
BISECT_STEPS = 40    # Binary search refinement per ray — 40 is plenty
R_MAX        = 2.0   # Max radius to search for boundary
VASE_HEIGHT_MM = 80.0  # Target print height in mm
VASE_SCALE_MM  = 60.0  # Target max diameter in mm
SMOOTH_ITERS   = 3    # Ring-level Laplacian smoothing passes
OUTPUT_FILE  = "julia_vase.stl"
```

### Algorithm

1. **Compute c-path**: `NUM_LAYERS` values of c from `compute_c(t)` for t in [0, 1].

2. **Per layer**: shoot `NUM_ANGLES` rays evenly spaced in [0, 2π]. For each ray angle θ:
   - Call `find_boundary_radius(theta, c)` → radius r
   - If None (disconnected set), interpolate from neighboring layers
   - Vertex position: `(r * cos(θ), r * sin(θ), z_layer)`

3. **Laplacian smoothing per ring**: for each layer's ring of vertices, apply:
   ```python
   for _ in range(SMOOTH_ITERS):
       new_ring = [(ring[(i-1)%N] + ring[i] + ring[(i+1)%N]) / 3 for i in range(N)]
       ring = new_ring
   ```
   Apply in XY only — don't change Z.

4. **Scale to physical dimensions**: after all rings are computed, normalize XY to `VASE_SCALE_MM/2` max radius, Z to `VASE_HEIGHT_MM`.

5. **Build mesh**:
   - Between each pair of adjacent rings (layer i, layer i+1), create quad faces: `[i*N+j, i*N+(j+1)%N, (i+1)*N+(j+1)%N, (i+1)*N+j]` — split each into two triangles
   - Cap bottom: centroid at (0, 0, 0); fan triangles from centroid to each edge of ring 0
   - Cap top: centroid at (0, 0, VASE_HEIGHT_MM); fan triangles from centroid to each edge of last ring
   - Ensure consistent winding (outward normals)

6. **Export STL**: use trimesh or numpy-stl. If trimesh is available, run `mesh.is_watertight` before export and print a warning if False.

7. **Print summary**: layer count, vertex count, face count, bounding box, watertight status.

### Quality targets

| Metric | Target |
|--------|--------|
| Watertight | Yes |
| Manifold | Yes (no non-manifold edges) |
| Layer count | ≥ 200 |
| Angles per ring | ≥ 512 |
| Max bisect refinement | 40 steps |
| Physical height | 80mm |
| Physical max diameter | ~60mm |
| STL file size | ~15–40 MB (binary STL) |

---

## What to NOT do

- Do not use Blender (`import bpy`) — this must run standalone
- Do not use PIL/OpenCV grid sampling for boundary detection
- Do not produce a point cloud (PLY) — the output must be a closed triangle mesh STL
- Do not use `marching cubes` — it produces isosurface meshes from voxel grids, which don't capture the true fractal boundary as cleanly as polar ray tracing
- Do not guess at c values — use the teardrop path formula above; it is tested and correct

---

## File locations for reference

- local Blender experiment files outside this repository — most refined earlier versions used during development
- local Blender experiment files outside this repository — similar earlier mesh approach
- `archive/legacy-scripts/stacked-julia.py` — older grid-sampling approach (produces PLY point clouds, not used in final version)
- repository root — working directory for the cleaned package

---

## Success criteria

Running `python julia_vase.py` should:
1. Complete in under 5 minutes on an M-series Mac
2. Produce `julia_vase.stl` in the working directory
3. Print "Watertight: True" to stdout
4. Open in PrusaSlicer/Bambu Studio and slice cleanly in vase mode without errors
5. Show a vase with visibly evolving Julia set cross-sections — lobed at the equator, round at top and bottom
