import numpy as np
from stl import mesh

def height_map_to_3d(image, scale):
    width, height = image.size
    pixels = np.array(image)

    # Create coordinate grid
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    x, y = np.meshgrid(x, y)
    z = pixels / 255.0 * scale  # Scale the height

    # Flatten arrays
    x = x.flatten()
    y = y.flatten()
    z = z.flatten()

    # Stack coordinates
    vertices = np.column_stack((x, y, z))

    # Generate faces
    faces = []
    for i in range(width - 1):
        for j in range(height - 1):
            idx = i + j * width
            faces.append([idx, idx + 1, idx + width])
            faces.append([idx + 1, idx + width + 1, idx + width])

    faces = np.array(faces)

    # Create the mesh
    surface = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            surface.vectors[i][j] = vertices[f[j], :]

    return surface

# Generate the 3D mesh from the height map
scale = 10  # Height scaling factor
surface_mesh = height_map_to_3d(julia_image, scale)
surface_mesh.save('julia_set.stl')
