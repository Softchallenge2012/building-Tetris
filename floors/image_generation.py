import base64
import io
import os
from PIL import Image
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from google import genai

def encode_image(image_path: str) -> str:
    """Helper function to convert local image files to base64."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def trim_white_margins(image: Image.Image, threshold: int = 245, keep_canvas_size: bool = False) -> Image.Image:
    """Remove white/empty margins around the subject and keep only the actual building block."""
    rgba = image.convert("RGBA")
    width, height = rgba.size
    bbox = None

    for y in range(height):
        for x in range(width):
            r, g, b, a = rgba.getpixel((x, y))
            if a > 0 and not (r > threshold and g > threshold and b > threshold):
                if bbox is None:
                    bbox = [x, y, x, y]
                else:
                    bbox[0] = min(bbox[0], x)
                    bbox[1] = min(bbox[1], y)
                    bbox[2] = max(bbox[2], x)
                    bbox[3] = max(bbox[3], y)

    if bbox is None:
        return image

    left, top, right, bottom = bbox
    cropped = image.crop((left, top, right + 1, bottom + 1))
    if keep_canvas_size:
        return cropped.resize((width, height), Image.LANCZOS)
    return cropped


def generate_polished_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_dir = os.path.abspath(os.path.join(base_dir, "..", "outputs"))

    # 1. Initialize the text model and image generation client
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    client = genai.Client()

    pattern_ref = os.path.join(outputs_dir, "patterns.jpeg")

    views = [
        {"name": "South", "file": os.path.join(outputs_dir, "elevation_bottom_south.png"), "out_name": "facade_elevation_south.png"},
        {"name": "North", "file": os.path.join(outputs_dir, "elevation_top_north.png"), "out_name": "facade_elevation_north.png"},
        {"name": "West", "file": os.path.join(outputs_dir, "elevation_left_west.png"), "out_name": "facade_elevation_west.png"},
        {"name": "East", "file": os.path.join(outputs_dir, "elevation_right_east.png"), "out_name": "facade_elevation_east.png"},
    ]

    # 2. Process and generate the four views separately
    for idx, view in enumerate(views):
        print(f"=== Processing {view['name']} View ({idx + 1}/4) ===")
        
        pattern_b64 = encode_image(pattern_ref)
        elevation_b64 = encode_image(view["file"])

        # Read the elevation diagram and remove any white border so only the building block remains
        with Image.open(view["file"]) as elev_im:
            elev_im = trim_white_margins(elev_im, keep_canvas_size=False)
            elev_w, elev_h = elev_im.size
        aspect_ratio = f"{elev_w}:{elev_h}"

        content_payload = [
            {
                "type": "text",
                "text": (
                    f"Given the attached {view['name']} building side view, "
                    "the small square elements are the windows. Only change the color of these window squares to create an arch pattern that follows the reference image. "
                    "Keep every other part of the building, façade, structure, and background exactly the same; do not alter the building shape, framing, walls, lines, or any non-window elements. "
                    "Preserve the original design and only recolor the windows into the rainbow/arch pattern."
                )
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{pattern_b64}"}
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{elevation_b64}"}
            }
        ]

        # Synthesize prompt for this specific view
        message = HumanMessage(content=content_payload)
        response = llm.invoke([message])
        generated_prompt = str(response.content)
        print(f"Synthesized Prompt for {view['name']} View:\n{generated_prompt}\n")

        # Append hard size constraint to the generated prompt
        size_suffix = (
            f" OUTPUT SIZE: The image must be exactly {elev_w} pixels wide by {elev_h} pixels tall "
            f"(aspect ratio {aspect_ratio}), matching the elevation diagram dimensions precisely."
        )
        generated_prompt += size_suffix

        # Generate image for this view
        img_response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=generated_prompt
        )

        # Save output images, resized to exactly match the elevation diagram
        file_path = os.path.join(outputs_dir, view["out_name"])
        file_path_num = os.path.join(outputs_dir, f"facade_elevation_{idx + 1}.png")
        
        for part in img_response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                img_data = part.inline_data.data
                img_bytes = base64.b64decode(img_data) if isinstance(img_data, str) else img_data
                image = Image.open(io.BytesIO(img_bytes))
                # Crop away any white border and keep only the building block itself
                image = trim_white_margins(image, keep_canvas_size=False)
                image = image.resize((elev_w, elev_h), Image.LANCZOS)
                image.save(file_path)
                image.save(file_path_num)
                print(f"Saved {view['name']} view image to: {file_path} and {file_path_num} (size: {elev_w}×{elev_h})\n")

if __name__ == '__main__':
    generate_polished_images()