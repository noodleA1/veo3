"""
Veo3 API - FastAPI endpoint for generating Veo3 prompts
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import base64
import io
from PIL import Image
from dotenv import load_dotenv
import replicate
import google.generativeai as genai
from typing import Optional

load_dotenv()

# Configure APIs
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not REPLICATE_API_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing required API keys in .env file")

genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-pro')

# Create FastAPI app
app = FastAPI(
    title="Veo3 Prompt Generator API",
    description="Generate Veo3 video prompts from images",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL image to base64"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def analyze_image_for_annotations(image: Image.Image) -> dict:
    """Analyze image and generate annotation instructions"""
    try:
        prompt = """
        Analyze this image for video storyboarding. Provide a detailed analysis with TWO outputs:

        1. SCENE OVERVIEW - Analyze the image and identify:
           - Main subjects and their potential motion paths
           - Camera movement opportunities (pan, zoom, track, arc)
           - Key focal points and composition elements
           - Lighting and mood
           - Foreground, midground, background elements

        2. STORYBOARD ANNOTATION INSTRUCTIONS - Create specific markup instructions:
           - Identify 3-5 elements that should move or animate
           - For each element, specify:
             * What it is and where it's located
             * How it should move (direction, speed, path)
             * What color annotation to use (RED for hero elements, BLUE for camera, GREEN for secondary, ORANGE for timing)
             * Specific arrow types and labels

        Return a JSON response like this:
        {
          "scene_overview": {
            "description": "Detailed 2-3 sentence scene description",
            "main_subject": "Primary focus and its location",
            "secondary_elements": ["element1", "element2"],
            "mood": "Emotional tone",
            "lighting": "Quality and direction",
            "camera_opportunities": "Possible camera movements",
            "motion_potential": "What could move and how"
          },
          "annotation_instructions": {
            "hero_element": {
              "what": "The main subject (e.g., boat, person, car)",
              "location": "Where in frame (e.g., center-left)",
              "motion": "How it moves (e.g., drifts right slowly)",
              "annotation": "RED CIRCLE around [element]",
              "arrow": "Curved RED ARROW showing path to the right",
              "label": "HERO MOVES → 3 SEC"
            },
            "camera_motion": {
              "type": "Camera movement type (e.g., arc, dolly, pan)",
              "path": "Movement description",
              "annotation": "BLUE DOTTED LINE showing path",
              "arrows": "BLUE ARROWS at key points",
              "label": "CAMERA ARCS 90°"
            },
            "secondary_elements": [
              {
                "what": "Secondary element",
                "motion": "Its movement",
                "annotation": "GREEN BOX or CIRCLE",
                "label": "ELEMENT ACTION"
              }
            ],
            "timing": {
              "duration": "8 seconds",
              "annotation": "ORANGE TEXT top-right",
              "label": "SCENE 1 - 8 SEC"
            }
          }
        }
        """
        
        response = vision_model.generate_content([image, prompt])
        json_text = response.text
        
        # Extract JSON from response
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "{" in json_text:
            json_text = json_text[json_text.find("{"):json_text.rfind("}")+1]
        
        return json.loads(json_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


def create_annotated_image(image: Image.Image, instructions: dict) -> Image.Image:
    """Create AI-generated annotations using Flux"""
    try:
        # Build natural language prompt for Flux Kontext
        ann_inst = instructions.get("annotation_instructions", {})
        
        prompt_parts = [
            "Keep the original photo unchanged. Only add storyboard markup overlays.",
            "Draw colored annotation marks as an overlay on top of the existing photo:",
            "IMPORTANT: Do NOT recreate or modify the base image - only add annotations.",
            ""
        ]
        
        # Hero element
        if 'hero_element' in ann_inst:
            hero = ann_inst['hero_element']
            prompt_parts.append(f"1. Draw a thick {hero.get('annotation', 'RED CIRCLE around main subject')}")
            prompt_parts.append(f"   Add {hero.get('arrow', 'RED ARROW showing movement')}")
            prompt_parts.append(f"   Label: '{hero.get('label', 'HERO MOVES')}'")
        
        # Camera motion
        if 'camera_motion' in ann_inst:
            cam = ann_inst['camera_motion']
            prompt_parts.append(f"2. Draw {cam.get('annotation', 'BLUE DOTTED LINE for camera path')}")
            prompt_parts.append(f"   Add {cam.get('arrows', 'BLUE ARROWS showing direction')}")
            prompt_parts.append(f"   Label: '{cam.get('label', 'CAMERA MOTION')}'")
        
        # Secondary elements
        if 'secondary_elements' in ann_inst:
            for i, elem in enumerate(ann_inst['secondary_elements'], 3):
                prompt_parts.append(f"{i}. {elem.get('annotation', 'GREEN annotation')}")
                prompt_parts.append(f"   Label: '{elem.get('label', 'ELEMENT')}'")
        
        # Timing
        if 'timing' in ann_inst:
            timing = ann_inst['timing']
            prompt_parts.append(f"Add {timing.get('annotation', 'ORANGE TEXT')} with '{timing.get('label', 'TIMING')}'")
        
        prompt_parts.extend([
            "",
            "Use colored markers for all annotations.",
            "Preserve the original photo completely - only add overlay markings."
        ])
        
        annotation_prompt = "\n".join(prompt_parts)
        
        # Convert image to base64
        img_data_url = f"data:image/png;base64,{image_to_base64(image)}"
        
        # Run Flux Kontext
        output = replicate.run(
            "black-forest-labs/flux-kontext-max",
            input={
                "prompt": annotation_prompt,
                "input_image": img_data_url,
                "guidance_scale": 3.5,  # Lower guidance to preserve original more
                "num_inference_steps": 28  # Standard steps for quality
            }
        )
        
        if output:
            import requests
            if hasattr(output, 'url'):
                image_url = output.url
            elif hasattr(output, '__iter__') and len(list(output)) > 0:
                first_item = list(output)[0]
                image_url = first_item.url if hasattr(first_item, 'url') else str(first_item)
            else:
                image_url = str(output)
            
            response = requests.get(image_url)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                raise Exception(f"Failed to download annotated image: {response.status_code}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Annotation error: {str(e)}")


def generate_veo3_json(annotated_image: Image.Image, user_prompt: str, analysis: dict) -> dict:
    """Generate final Veo3 JSON from annotated image and prompt"""
    try:
        analysis_prompt = f"""
        Analyze this storyboard-annotated image and the user's video description to create a comprehensive Veo3 video generation specification.

        The image contains colored storyboard annotations:
        - RED markings: Primary subject movement paths
        - BLUE markings: Camera movement indicators  
        - GREEN markings: Secondary elements and focal points
        - ORANGE markings: Timing and scene information

        User's video request: {user_prompt}

        Generate a detailed JSON for Veo3 video generation that incorporates BOTH the storyboard annotations AND the user's vision:

        {{
          "prompt": "Main video generation prompt combining scene + user request",
          "scene_description": "Detailed 2-3 sentence description incorporating annotated elements",
          "camera": {{
            "initial_position": "Starting camera position",
            "movement": "Camera movement following BLUE annotations",
            "focal_length": "Lens choice (e.g., 24mm wide, 50mm normal, 85mm portrait)",
            "depth_of_field": "Shallow/deep based on scene needs",
            "stabilization": "Smooth/handheld/dynamic"
          }},
          "subject_motion": {{
            "primary": "Main subject movement following RED annotations",
            "path": "Specific path and timing from annotations",
            "secondary_elements": "Other moving elements from GREEN annotations"
          }},
          "visual_style": {{
            "treatment": "Cinematic/documentary/artistic based on mood",
            "color_grading": "Color treatment matching scene mood",
            "lighting": "Natural/dramatic/soft based on image"
          }},
          "timing": {{
            "duration_seconds": 8,
            "pacing": "Rhythm based on annotation timing",
            "key_moments": "When important actions occur"
          }},
          "technical_specs": {{
            "aspect_ratio": "16:9",
            "resolution": "4K",
            "frame_rate": "24fps cinematic",
            "motion_blur": "Natural motion blur"
          }},
          "audio_hints": {{
            "ambience": "Environmental sounds matching scene",
            "music_style": "Mood-appropriate score",
            "sound_effects": ["specific sounds for actions"]
          }},
          "storyboard_integration": {{
            "follow_red_paths": "Primary motion as marked",
            "follow_blue_camera": "Camera movement as indicated",
            "highlight_green_elements": "Ensure focal points are featured",
            "respect_orange_timing": "Match annotated duration and pacing"
          }},
          "negative_prompt": "Avoid: shaky camera, abrupt cuts, unnatural motion",
          "user_intent_integration": "{user_prompt} - incorporated throughout"
        }}

        IMPORTANT: Read the actual annotations in the image and incorporate those specific movements, paths, and timings into your JSON response.
        """
        
        response = vision_model.generate_content([annotated_image, analysis_prompt])
        json_text = response.text
        
        # Extract JSON from response
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "{" in json_text:
            json_text = json_text[json_text.find("{"):json_text.rfind("}")+1]
        
        return json.loads(json_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veo3 generation error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Veo3 Prompt Generator API",
        "version": "1.0.0",
        "endpoints": {
            "/generate-veo3": "POST - Generate Veo3 JSON from image and prompt",
            "/docs": "GET - Interactive API documentation"
        }
    }


@app.post("/generate-veo3")
async def generate_veo3(
    image: UploadFile = File(..., description="Image file to analyze"),
    prompt: str = Form(..., description="Video description prompt")
):
    """
    Generate Veo3 JSON from an image and text prompt
    
    Process:
    1. Analyze the image for storyboard opportunities
    2. Create AI annotations on the image
    3. Generate comprehensive Veo3 JSON based on annotations and user prompt
    """
    try:
        # Validate image file
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Step 1: Analyze image
        analysis = analyze_image_for_annotations(pil_image)
        
        # Step 2: Create annotated image
        annotated_image = create_annotated_image(pil_image, analysis)
        
        # Step 3: Generate Veo3 JSON
        veo3_json = generate_veo3_json(annotated_image, prompt, analysis)
        
        # Return response
        return JSONResponse(
            content={
                "status": "success",
                "veo3_prompt": veo3_json,
                "scene_analysis": analysis.get("scene_overview", {}),
                "annotation_applied": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)