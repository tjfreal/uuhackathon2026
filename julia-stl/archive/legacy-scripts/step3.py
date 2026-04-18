from math import pi
import numpy as np
from stl import mesh

def revolve_profile(image, num_steps):
    width, height = image.size
    pixels = np.array(image)
    center_column = pixels[:, width // 2]

    theta = np.linspace(0, 2 * pi, num_steps)
    z = np.linspace(0, height, height)
    radii = center_column / 255.0  # Normalize radii

    vertices = []
    for i in range(height):
        for angle in theta:
            x = radii[i] * np.cos(angle)
            y = radii[i] * np.sin(angle)
            vertices.append([x, y, z[i]])

    vertices = np.array(vertices)

    # Generate faces
    faces = []
    steps = num_steps
    for i in range(height - 1):
        for j in range(steps):
            next_j = (j + 1) % steps
            idx = i * steps + j
            faces.append([idx, idx + steps, idx + steps + next_j - j])
            faces.append([idx, idx + steps + next_j - j, idx + next_j])

    faces = np.array(faces)

    # Create the mesh
    vase = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            vase.vectors[i][j] = vertices[f[j], :]

    return vase

# Generate the revolved vase mesh
num_steps = 100  # Number of steps around the circle
vase_mesh = revolve_profile(julia_image, num_steps)
vase_mesh.save('julia_vase.stl')
