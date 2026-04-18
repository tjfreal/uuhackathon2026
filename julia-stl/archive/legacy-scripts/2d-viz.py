from PIL import Image
import numpy as np

# Parameters
width, height = 500, 500  # Image size
iterations = 100  # Max number of iterations
c = 0.355 + 0.355j  # Julia constant (can vary)

def generate_julia_set(width, height, c, iterations):
    """Generates a 2D Julia set slice."""
    # Create an empty array for pixel values
    image = np.zeros((height, width), dtype=np.uint8)

    for x in range(width):
        for y in range(height):
            zx = 3.0 * (x - width / 2) / (width / 2)  # Scale x to [-1.5, 1.5]
            zy = 3.0 * (y - height / 2) / (height / 2)  # Scale y to [-1.5, 1.5]
            z = complex(zx, zy)
            count = 0

            while abs(z) < 2 and count < iterations:
                z = z**2 + c
                count += 1

            # Map iterations to grayscale (0-255)
            image[y, x] = 255 - int(count * 255 / iterations)

    return Image.fromarray(image)

# Generate and save a slice
julia_image = generate_julia_set(width, height, c, iterations)
julia_image.show()  # Show the image
julia_image.save("julia_slice.png")  # Save the image
