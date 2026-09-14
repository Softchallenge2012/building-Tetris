import base64
import io
import os
from PIL import Image
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai

def encode_image(image_path: str) -> str:
    """Helper function to convert local image files to base64."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def generate_polished_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_dir = os.path.abspath(os.path.join(base_dir, "..", "outputs"))

    # 1. Initialize Gemini models
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
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
        
        content_payload = [
            {
                "type": "text",
                "text": (
                    f"Given the attached {view['name']} building elevation diagram and the arch pattern reference image, "
                    f"generate a detailed image generation prompt for a futuristic and modern 17-story building elevation for the {view['name']} face. "
                    "The instruction requires changing the building exterior colors to metallic silver/futuristic finish and "
                    "linking the central windows into the arched rainbow pattern shown in the reference image. "
                    "CRITICAL REQUIREMENT 1: The prompt MUST mandate that the output image features ONLY the building structure itself against a pure, seamless solid white background, with NO sky, NO clouds, NO ground/landscape, NO trees, and NO surrounding environment or background elements. "
                    "CRITICAL REQUIREMENT 2: The output needs to have 17 stories for this view!"
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

        # Generate image for this view
        img_response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=generated_prompt
        )

        # Save output images
        file_path = os.path.join(outputs_dir, view["out_name"])
        file_path_num = os.path.join(outputs_dir, f"facade_elevation_{idx + 1}.png")
        
        for part in img_response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                img_data = part.inline_data.data
                img_bytes = base64.b64decode(img_data) if isinstance(img_data, str) else img_data
                image = Image.open(io.BytesIO(img_bytes))
                image.save(file_path)
                image.save(file_path_num)
                print(f"Saved {view['name']} view image to: {file_path} and {file_path_num}\n")

if __name__ == '__main__':
    generate_polished_images()