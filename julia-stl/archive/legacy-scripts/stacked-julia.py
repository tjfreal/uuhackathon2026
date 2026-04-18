from PIL import Image
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

def process_image_to_points(image):
    print("Converting image to boundary points...")
    binary_image = np.array(image) < 128
    contours, _ = cv2.findContours(binary_image.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    points = np.vstack([contour[:, 0, :] for contour in contours])
    print(f"Extracted {len(points)} points from contours.")
    return points

def save_to_ply(points, output_path):
    print(f"Saving {len(points)} points to PLY file at {output_path}...")
    with open(output_path, "w") as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"element vertex {len(points)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("end_header\n")
        for x, y, z in points:
            file.write(f"{x} {y} {z}\n")
    print(f"PLY file saved to {output_path}.")

def stack_julia_sets(
    width, height, zoom, move_x, move_y, base_c, max_iter, stack_count, c_increment, output_ply
):
    all_points = []

    for layer in range(stack_count):
        print(f"Generating layer {layer + 1}/{stack_count}...")
        c = base_c + (layer * c_increment)
        print(f"Using c = {c}")

        image = generate_julia_set(width, height, zoom, move_x, move_y, c, max_iter)
        points = process_image_to_points(image)

        # Add a Z-coordinate for the layer
        points_with_z = [(x, y, layer) for x, y in points]
        all_points.extend(points_with_z)

        # Visualize the layer
        print(f"Visualizing layer {layer + 1}...")
        plt.figure(figsize=(8, 8))
        plt.scatter([p[0] for p in points_with_z], [p[1] for p in points_with_z], s=1, label=f"Layer {layer + 1}")
        plt.gca().invert_yaxis()
        plt.title(f"Julia Set Layer {layer + 1}")
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
        plt.legend()
        #plt.show()

    # Save all stacked points to a PLY file
    save_to_ply(all_points, output_ply)

# Adjustable parameters
width = 800
height = 800
zoom = 1
move_x = 0.0
move_y = 0.0
#base_c = complex(-0.7, 0.27015)  # Starting value of c
base_c = 0
max_iter = 300
stack_count = 75  # Number of layers to stack
#c_increment = complex(0.0, -0.01)  # Increment applied to c at each layer
c_increment = complex(-0.02, 0.01)
output_ply = "stacked_julia_set2.ply"

# Generate and save stacked Julia sets
stack_julia_sets(width, height, zoom, move_x, move_y, base_c, max_iter, stack_count, c_increment, output_ply)
