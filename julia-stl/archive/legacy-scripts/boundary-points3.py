from PIL import Image, ImageFilter
import numpy as np
import matplotlib.pyplot as plt
import cv2
import trimesh

def generate_julia_set(width, height, zoom, move_x, move_y, c, max_iter):
    # Create a new image in grayscale mode
    image = Image.new("L", (width, height))
    pixels = image.load()

    for x in range(width):
        for y in range(height):
            # Convert pixel coordinate to complex number
            zx = 1.5 * (x - width / 2) / (0.5 * zoom * width) + move_x
            zy = 1.0 * (y - height / 2) / (0.5 * zoom * height) + move_y
            z = complex(zx, zy)

            iteration = 0
            while abs(z) < 4 and iteration < max_iter:
                z = z**2 + c
                iteration += 1

            # Map the number of iterations to a grayscale value
            color = 255 - int(iteration * 255 / max_iter)
            pixels[x, y] = color

    return image

def process_image(image_path):
    # Open the image
    print("Loading image for processing...")
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Image at {image_path} not found.")

    # Apply binary thresholding
    print("Applying binary thresholding...")
    _, binary_image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)

    # Apply edge detection
    print("Detecting edges...")
    edges = cv2.Canny(binary_image, 100, 200)

    # Find coordinates of edge pixels
    print("Extracting boundary points...")
    boundary_points = np.column_stack(np.where(edges > 0))

    # Log identified points
    print(f"Identified {len(boundary_points)} boundary points.")

    # Plot the boundary points for visualization
    if len(boundary_points) > 0:
        print("Plotting boundary points...")
        x_coords, y_coords = boundary_points[:, 1], boundary_points[:, 0]
        plt.figure(figsize=(8, 8))
        plt.scatter(x_coords, y_coords, s=0.5, color="red")
        plt.gca().invert_yaxis()
        plt.title("Boundary of the Julia Set")
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
        plt.show()

    return boundary_points

def export_to_stl(boundary_points, output_path):
    print("Exporting boundary points to STL...")
    vertices = [(x, y, 0) for x, y in boundary_points]
    faces = []
    for i in range(len(vertices) - 1):
        faces.append([i, i + 1, (i + 2) % len(vertices)])

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh.export(output_path)
    print(f"STL file saved to {output_path}")

def export_to_ply(boundary_points, output_path):
    print("Exporting boundary points to PLY...")
    with open(output_path, "w") as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"element vertex {len(boundary_points)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("end_header\n")
        for x, y in boundary_points:
            file.write(f"{x} {y} 0\n")
    print(f"PLY file saved to {output_path}")

def process_ply_for_perimeter(ply_path, clearance_threshold=5):
    print("Processing PLY file to extract detailed perimeter points...")
    # Load PLY file
    points = []
    with open(ply_path, "r") as file:
        header = True
        for line in file:
            if header:
                if line.strip() == "end_header":
                    header = False
                continue
            x, y, z = map(float, line.split())
            points.append((x, y))

    points = np.array(points)

    print("Filtering perimeter points based on clearance...")
    perimeter_points = []
    for point in points:
        neighbors = points[np.linalg.norm(points - point, axis=1) < clearance_threshold]
        if len(neighbors) < 8:  # Adjust threshold for neighbor count to detect perimeter
            perimeter_points.append(point)

    perimeter_points = np.array(perimeter_points)
    print(f"Extracted {len(perimeter_points)} perimeter points.")

    # Plot perimeter points
    plt.figure(figsize=(8, 8))
    plt.scatter(points[:, 0], points[:, 1], s=0.5, color="blue", label="All Points")
    plt.plot(perimeter_points[:, 0], perimeter_points[:, 1], color="red", label="Perimeter")
    plt.gca().invert_yaxis()
    plt.title("Refined Perimeter of the Shape")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.legend()
    plt.show()

    return perimeter_points

# Parameters
width, height = 800, 800
zoom = 1
move_x, move_y = 0.0, 0.0
c = complex(-0.7, 0.27015)
max_iter = 300

# Generate and save the Julia set image
julia_image = generate_julia_set(width, height, zoom, move_x, move_y, c, max_iter)
julia_image.save("julia_set.png")

# Process the image and get boundary points
boundary_points = process_image("julia_set.png")

# Export boundary points
export_to_stl(boundary_points, "julia_set_boundary.stl")
export_to_ply(boundary_points, "julia_set_boundary.ply")

# Process PLY file for refined perimeter points
perimeter_points = process_ply_for_perimeter("julia_set_boundary.ply", clearance_threshold=5)

export_to_ply(perimeter_points, "julia_set_perimeter.ply")
