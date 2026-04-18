from PIL import Image

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

# Parameters
width, height = 800, 800
zoom = 1
move_x, move_y = 0.0, 0.0
c = complex(-0.7, 0.27015)
max_iter = 300

# Generate and save the Julia set image
julia_image = generate_julia_set(width, height, zoom, move_x, move_y, c, max_iter)
julia_image.save("julia_set.png")
