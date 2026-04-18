import math
import time
import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class VaseConfig:
    num_layers: int = 180
    num_angles: int = 256
    max_iter: int = 220
    scan_steps: int = 48
    boundary_refine_steps: int = 20
    ring_smoothing_iters: int = 3
    layer_smoothing_passes: int = 1
    radial_limit: float = 2.2
    vase_height_mm: float = 200.0
    vase_diameter_mm: float = 150.0
    base_radius_ratio: float = 0.62
    bulge_strength: float = 0.085
    modulation_peak: float = 0.50
    modulation_rise_end: float = 0.72
    modulation_fall_start: float = 0.68
    detail_power: float = 2.6
    detail_strength: float = 0.69
    outward_weight: float = 0.28
    inward_weight: float = 0.92
    detail_start: float = 0.0
    detail_end: float = 1.0
    c_real_scale: float = 0.32
    c_imag_scale: float = 0.27
    output_path: str = "assets/models/julia_vase.stl"
    preview_path: str = "assets/previews/julia_vase_preview.stl"
    preview_mode: bool = False


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def layer_profile(t: float, power: float) -> float:
    return math.sin(math.pi * t) ** power


def body_radius_ratio(t: float, config: VaseConfig) -> float:
    bulge = layer_profile(t, 1.15)
    return config.base_radius_ratio * (1.0 + config.bulge_strength * bulge)


def symmetric_progress(t: float) -> float:
    return 1.0 - abs(2.0 * t - 1.0)


def modulation_envelope(t: float, config: VaseConfig) -> float:
    s = symmetric_progress(t)
    if s <= config.modulation_rise_end:
        rise = smoothstep(s / max(1e-6, config.modulation_rise_end))
        return config.modulation_peak * rise
    return config.modulation_peak


def julia_survives(z: complex, c: complex, max_iter: int) -> bool:
    for _ in range(max_iter):
        if z.real * z.real + z.imag * z.imag > 4.0:
            return False
        z = z * z + c
    return True


def boundary_radius(theta: float, c: complex, config: VaseConfig) -> float:
    if not julia_survives(0j, c, config.max_iter):
        return 0.0

    direction = complex(math.cos(theta), math.sin(theta))
    r_inner = 0.0

    for step in range(1, config.scan_steps + 1):
        radius = (step / config.scan_steps) * config.radial_limit
        if julia_survives(radius * direction, c, config.max_iter):
            r_inner = radius
            continue

        r_low = r_inner
        r_high = radius
        for _ in range(config.boundary_refine_steps):
            r_mid = 0.5 * (r_low + r_high)
            if julia_survives(r_mid * direction, c, config.max_iter):
                r_low = r_mid
            else:
                r_high = r_mid
        return 0.5 * (r_low + r_high)

    return config.radial_limit


def smooth_ring(radii: np.ndarray, iterations: int) -> np.ndarray:
    smoothed = radii.copy()
    for _ in range(iterations):
        smoothed = (
            np.roll(smoothed, 1) + smoothed + np.roll(smoothed, -1)
        ) / 3.0
    return smoothed


def smooth_layers(rings: np.ndarray, passes: int) -> np.ndarray:
    smoothed = rings.copy()
    for _ in range(passes):
        interior = (
            smoothed[:-2] + smoothed[1:-1] + smoothed[2:]
        ) / 3.0
        smoothed[1:-1] = interior
    return smoothed


def shape_ring(
    radii: np.ndarray, layer_index: int, total_layers: int, config: VaseConfig
) -> np.ndarray:
    t = layer_index / max(1, total_layers - 1)
    detail_mix = modulation_envelope(t, config) * config.detail_strength

    mean_radius = float(np.mean(radii))
    if mean_radius <= 1e-9:
        normalized = np.ones_like(radii)
    else:
        normalized = radii / mean_radius

    circle_radius = config.radial_limit * body_radius_ratio(t, config)
    centered = normalized - 1.0
    weighted = np.where(
        centered >= 0.0,
        centered * config.outward_weight,
        centered * config.inward_weight,
    )
    shaped = circle_radius * (1.0 + detail_mix * weighted)
    return shaped


def sample_ring(layer_index: int, total_layers: int, config: VaseConfig) -> np.ndarray:
    t = layer_index / max(1, total_layers - 1)
    c = compute_c_from_config(t, config)
    radii = np.zeros(config.num_angles, dtype=np.float64)

    for angle_index in range(config.num_angles):
        theta = (2.0 * math.pi * angle_index) / config.num_angles
        radii[angle_index] = boundary_radius(theta, c, config)

    radii = smooth_ring(radii, config.ring_smoothing_iters)
    radii = shape_ring(radii, layer_index, total_layers, config)
    return radii


def compute_c_from_config(t: float, config: VaseConfig) -> complex:
    s = symmetric_progress(t)
    theta = math.pi * s
    real = config.c_real_scale * math.sin(theta)
    imag = config.c_imag_scale * (math.cos(theta) - 1.0)
    return complex(real, imag)


def build_rings(config: VaseConfig) -> np.ndarray:
    rings = np.zeros((config.num_layers, config.num_angles), dtype=np.float64)
    for layer_index in range(config.num_layers):
        print(f"Sampling layer {layer_index + 1}/{config.num_layers}...")
        rings[layer_index] = sample_ring(layer_index, config.num_layers, config)
    rings = smooth_layers(rings, config.layer_smoothing_passes)
    return rings


def rings_to_vertices(rings: np.ndarray, config: VaseConfig) -> np.ndarray:
    max_radius = float(np.max(rings))
    if max_radius <= 0.0:
        raise ValueError("No valid ring radii were generated.")

    xy_scale = (config.vase_diameter_mm * 0.5) / max_radius
    z_values = np.linspace(0.0, config.vase_height_mm, config.num_layers)
    angles = np.linspace(0.0, 2.0 * math.pi, config.num_angles, endpoint=False)

    vertices = []
    for layer_index, z in enumerate(z_values):
        scaled = rings[layer_index] * xy_scale
        for radius, theta in zip(scaled, angles):
            vertices.append(
                [radius * math.cos(theta), radius * math.sin(theta), z]
            )

    bottom_center = [0.0, 0.0, 0.0]
    top_center = [0.0, 0.0, config.vase_height_mm]
    vertices.append(bottom_center)
    vertices.append(top_center)
    return np.asarray(vertices, dtype=np.float64)


def build_faces(config: VaseConfig) -> np.ndarray:
    faces = []
    ring_size = config.num_angles
    total_ring_vertices = config.num_layers * ring_size
    bottom_center_index = total_ring_vertices
    top_center_index = total_ring_vertices + 1

    for layer in range(config.num_layers - 1):
        base = layer * ring_size
        next_base = (layer + 1) * ring_size
        for angle in range(ring_size):
            next_angle = (angle + 1) % ring_size
            a = base + angle
            b = base + next_angle
            c = next_base + angle
            d = next_base + next_angle
            faces.append([a, c, b])
            faces.append([b, c, d])

    for angle in range(ring_size):
        next_angle = (angle + 1) % ring_size
        faces.append([bottom_center_index, next_angle, angle])

    top_base = (config.num_layers - 1) * ring_size
    for angle in range(ring_size):
        next_angle = (angle + 1) % ring_size
        faces.append([top_center_index, top_base + angle, top_base + next_angle])

    return np.asarray(faces, dtype=np.int64)


def build_mesh(rings: np.ndarray, config: VaseConfig) -> trimesh.Trimesh:
    vertices = rings_to_vertices(rings, config)
    faces = build_faces(config)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.invert()
    return mesh


def export_mesh(mesh: trimesh.Trimesh, output_path: str) -> None:
    mesh.export(output_path, file_type="stl")


def print_summary(mesh: trimesh.Trimesh, config: VaseConfig, elapsed: float) -> None:
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    print("")
    print("Build summary")
    print(f"Layers: {config.num_layers}")
    print(f"Angles per layer: {config.num_angles}")
    print(f"Vertices: {len(mesh.vertices)}")
    print(f"Faces: {len(mesh.faces)}")
    print(
        "Bounding box mm: "
        f"{size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}"
    )
    print(f"Watertight: {mesh.is_watertight}")
    print(f"Output: {config.output_path}")
    print(f"Elapsed: {elapsed:.1f}s")


def resolve_config() -> VaseConfig:
    parser = argparse.ArgumentParser(description="Generate a Julia vase STL.")
    parser.add_argument("--preview", action="store_true", help="Use faster preview settings.")
    parser.add_argument("--layers", type=int, help="Override the number of Z layers.")
    parser.add_argument("--angles", type=int, help="Override the number of samples per ring.")
    parser.add_argument("--max-iter", type=int, help="Override the Julia iteration depth.")
    parser.add_argument("--scan-steps", type=int, help="Override the coarse radial scan steps.")
    parser.add_argument("--refine-steps", type=int, help="Override the binary refinement steps.")
    parser.add_argument("--base-radius", type=float, help="Override the base body radius ratio.")
    parser.add_argument("--bulge-strength", type=float, help="Override the gentle mid-body bulge strength.")
    parser.add_argument("--modulation-peak", type=float, help="Override the maximum Julia modulation envelope.")
    parser.add_argument("--detail-strength", type=float, help="Override Julia detail strength.")
    parser.add_argument("--outward-weight", type=float, help="Override outward deformation weight.")
    parser.add_argument("--inward-weight", type=float, help="Override inward deformation weight.")
    parser.add_argument("--rise-end", type=float, help="Override where Julia modulation reaches full strength.")
    parser.add_argument("--fall-start", type=float, help="Override where Julia modulation starts fading out.")
    parser.add_argument("--c-real", type=float, help="Override the Mandelbrot path real scale.")
    parser.add_argument("--c-imag", type=float, help="Override the Mandelbrot path imaginary scale.")
    parser.add_argument("--output", type=str, help="Override the output STL path.")
    args = parser.parse_args()

    config = VaseConfig(preview_mode=args.preview)
    if config.preview_mode:
        config.num_layers = 96
        config.num_angles = 160
        config.max_iter = 160
        config.scan_steps = 32
        config.boundary_refine_steps = 14
        config.output_path = config.preview_path

    if args.layers:
        config.num_layers = args.layers
    if args.angles:
        config.num_angles = args.angles
    if args.max_iter:
        config.max_iter = args.max_iter
    if args.scan_steps:
        config.scan_steps = args.scan_steps
    if args.refine_steps:
        config.boundary_refine_steps = args.refine_steps
    if args.base_radius is not None:
        config.base_radius_ratio = args.base_radius
    if args.bulge_strength is not None:
        config.bulge_strength = args.bulge_strength
    if args.modulation_peak is not None:
        config.modulation_peak = args.modulation_peak
    if args.detail_strength is not None:
        config.detail_strength = args.detail_strength
    if args.outward_weight is not None:
        config.outward_weight = args.outward_weight
    if args.inward_weight is not None:
        config.inward_weight = args.inward_weight
    if args.rise_end is not None:
        config.modulation_rise_end = args.rise_end
    if args.fall_start is not None:
        config.modulation_fall_start = args.fall_start
    if args.c_real is not None:
        config.c_real_scale = args.c_real
    if args.c_imag is not None:
        config.c_imag_scale = args.c_imag
    if args.output:
        config.output_path = args.output
    return config


def main() -> None:
    config = resolve_config()
    start = time.time()
    rings = build_rings(config)
    mesh = build_mesh(rings, config)

    output_path = Path(config.output_path)
    export_mesh(mesh, str(output_path))
    elapsed = time.time() - start
    print_summary(mesh, config, elapsed)


if __name__ == "__main__":
    main()
