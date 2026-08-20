import sys
import os
from PIL import Image

def main():
    if len(sys.argv) < 4:
        print("Usage: python compare.py <reference_image> <screenshot_image> <diff_output_image>")
        sys.exit(1)

    ref_path = sys.argv[1]
    shot_path = sys.argv[2]
    diff_path = sys.argv[3]

    if not os.path.exists(ref_path) or not os.path.exists(shot_path):
        print(f"Error: One or both input images do not exist.")
        sys.exit(1)

    # Open images and convert to RGBA
    ref_img = Image.open(ref_path).convert("RGBA")
    shot_img = Image.open(shot_path).convert("RGBA")

    # We use the shot image width as target (default is 1440)
    target_width = shot_img.width
    
    # Resize reference image to match width if needed, maintaining aspect ratio
    if ref_img.width != target_width:
        aspect_ratio = ref_img.height / ref_img.width
        new_height = int(target_width * aspect_ratio)
        ref_img = ref_img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        print(f"Resized reference image to {target_width}x{new_height}")

    # Pad both images to the same height (the max height) to allow comparison
    max_height = max(ref_img.height, shot_img.height)
    
    # Create white canvas for padding
    ref_padded = Image.new("RGBA", (target_width, max_height), (255, 255, 255, 255))
    ref_padded.paste(ref_img, (0, 0))

    shot_padded = Image.new("RGBA", (target_width, max_height), (255, 255, 255, 255))
    shot_padded.paste(shot_img, (0, 0))

    # Perform comparison
    ref_data = ref_padded.load()
    shot_data = shot_padded.load()

    diff_img = Image.new("RGBA", (target_width, max_height))
    diff_data = diff_img.load()

    mismatches = 0
    total_pixels = target_width * max_height

    # Pixel mismatch threshold (tolerance for compression artifacts or antialiasing)
    threshold = 20

    for y in range(max_height):
        for x in range(target_width):
            r1, g1, b1, a1 = ref_data[x, y]
            r2, g2, b2, a2 = shot_data[x, y]

            # Calculate absolute color differences
            diff_r = abs(r1 - r2)
            diff_g = abs(g1 - g2)
            diff_b = abs(b1 - b2)
            diff_a = abs(a1 - a2)

            if diff_r > threshold or diff_g > threshold or diff_b > threshold or diff_a > threshold:
                # Color mismatched pixels bright red
                diff_data[x, y] = (255, 0, 0, 255)
                mismatches += 1
            else:
                # Faded grayscale version of reference for matched pixels
                gray_val = int(0.299 * r1 + 0.587 * g1 + 0.114 * b1)
                diff_data[x, y] = (gray_val, gray_val, gray_val, 40)

    mismatch_percentage = (mismatches / total_pixels) * 100
    print(f"Mismatch: {mismatch_percentage:.2f}% ({mismatches} / {total_pixels} pixels)")

    # Save diff image
    diff_img.save(diff_path)
    print(f"Saved diff visualizer to {diff_path}")

if __name__ == "__main__":
    main()
