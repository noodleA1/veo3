"""
Veo3 Complete - All features, cleaner layout
"""

import gradio as gr
import os
import json
import base64
import io
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
import replicate
import google.generativeai as genai

load_dotenv()

# Configure APIs
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    vision_model = genai.GenerativeModel('gemini-1.5-pro')
else:
    vision_model = None


class Veo3State:
    def __init__(self):
        self.original_image = None
        self.ai_annotated_image = None
        self.manual_annotated_image = None
        self.annotation_instructions = None
        self.overview_data = None
    
    def get_current_image(self):
        """Get the most recent image in the pipeline"""
        return self.manual_annotated_image or self.ai_annotated_image or self.original_image


# We'll use Gradio's state management instead of global state


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL image to base64"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def generate_or_upload_image(image_upload, gen_prompt, state):
    """Handle both image upload and generation"""
    if image_upload is not None:
        state.original_image = image_upload
        return image_upload, "✅ Image uploaded", state
    
    if gen_prompt and gen_prompt.strip():
        if not REPLICATE_API_TOKEN:
            return None, "❌ Replicate API not configured"
        
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": gen_prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "png"
                }
            )
            
            if output and len(output) > 0:
                import requests
                response = requests.get(output[0])
                image = Image.open(io.BytesIO(response.content))
                state.original_image = image
                return image, "✅ Image generated", state
                
        except Exception as e:
            return None, f"❌ Generation error: {str(e)}", state
    
    return None, "❌ Please upload an image or enter a generation prompt", state


def analyze_for_annotations(image, state):
    """Analyze image and generate annotation instructions"""
    if image is None:
        return "", "", "❌ No image provided", state
    
    if not vision_model:
        return "", "", "❌ Gemini Vision API not configured", state
    
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
        
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "{" in json_text:
            json_text = json_text[json_text.find("{"):json_text.rfind("}")+1]
        
        # Parse and store
        data = json.loads(json_text)
        state.annotation_instructions = json_text
        state.overview_data = data.get("scene_overview", {})
        
        # Format overview for display
        overview = state.overview_data
        overview_text = f"""**Scene:** {overview.get('description', 'N/A')}
**Main Subject:** {overview.get('main_subject', 'N/A')}
**Mood:** {overview.get('mood', 'N/A')}
**Camera Options:** {overview.get('camera_opportunities', 'N/A')}
**Motion Potential:** {overview.get('motion_potential', 'N/A')}"""
        
        return overview_text, json_text, "✅ Analysis complete", state
        
    except Exception as e:
        return "", "", f"❌ Analysis error: {str(e)}", state


def create_ai_annotations(image, instructions, state):
    """Create AI-generated annotations using Flux"""
    if image is None:
        return None, "❌ No image provided", state
    
    if not instructions or instructions.strip() == "":
        return None, "❌ No annotation instructions", state
    
    if not REPLICATE_API_TOKEN:
        return None, "❌ Replicate API not configured", state
    
    try:
        instructions_dict = json.loads(instructions)
        
        # Build natural language prompt for Flux Kontext
        ann_inst = instructions_dict.get("annotation_instructions", {})
        
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
        
        img_data_url = f"data:image/png;base64,{image_to_base64(image)}"
        
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
                annotated_image = Image.open(io.BytesIO(response.content))
                state.ai_annotated_image = annotated_image
                return annotated_image, "✅ AI annotations created", state
            else:
                return None, f"❌ Failed to download annotated image: {response.status_code}", state
            
    except Exception as e:
        return None, f"❌ Annotation error: {str(e)}", state
    
    return None, "❌ Failed to create annotations", state


def save_manual_annotations(editor_data, state):
    """Save manual annotations from the editor"""
    if editor_data and "composite" in editor_data:
        state.manual_annotated_image = editor_data["composite"]
        return state.manual_annotated_image, "✅ Manual annotations saved", state
    return None, "❌ No manual annotations to save", state


def get_selected_image(choice, state):
    """Get image based on user choice"""
    if choice == "AI Annotated" and state.ai_annotated_image:
        return state.ai_annotated_image
    elif choice == "Manual Annotated" and state.manual_annotated_image:
        return state.manual_annotated_image
    else:
        return state.original_image

def generate_veo3_json(user_prompt, image_choice, state):
    """Generate final Veo3 JSON"""
    image = get_selected_image(image_choice, state)
    
    if image is None:
        return "", "❌ No image available"
    
    if not user_prompt or user_prompt.strip() == "":
        return "", "❌ Please describe your video"
    
    if not vision_model:
        return "", "❌ Vision API not configured"
    
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
        
        response = vision_model.generate_content([image, analysis_prompt])
        json_text = response.text
        
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "{" in json_text:
            json_text = json_text[json_text.find("{"):json_text.rfind("}")+1]
        
        json.loads(json_text)  # Validate JSON
        
        return json_text, "✅ Veo3 JSON generated"
        
    except Exception as e:
        return "", f"❌ Error: {str(e)}"


# Build the interface
with gr.Blocks(title="Veo3 Complete", theme=gr.themes.Soft()) as app:
    # Create state object for this session
    app_state = gr.State(Veo3State())
    
    gr.Markdown("# 🎬 Veo3 Prompt Generator - Complete Workflow")
    
    with gr.Row():
        # LEFT COLUMN - Controls
        with gr.Column(scale=1):
            # Step 1: Image Input
            gr.Markdown("### 1️⃣ Start with an Image")
            with gr.Tabs():
                with gr.TabItem("Upload"):
                    image_upload = gr.Image(type="pil", label="Upload Image")
                with gr.TabItem("Generate"):
                    gen_prompt = gr.Textbox(
                        label="Generate Image",
                        placeholder="A futuristic cityscape...",
                        lines=2
                    )
            
            process_btn = gr.Button("Process Image", variant="primary", size="lg")
            
            # Step 2: Annotation Controls
            gr.Markdown("### 2️⃣ Create Annotations")
            ai_annotate_btn = gr.Button("Generate AI Annotations", variant="secondary")
            
            # Step 3: Choose Image & Manual Annotations
            gr.Markdown("### 3️⃣ Choose Working Image")
            image_choice = gr.Radio(
                choices=["Original", "AI Annotated", "Manual Annotated"],
                value="Original",
                label="Select which image to work with"
            )
            
            gr.Markdown("### Optional: Add Manual Annotations")
            image_editor = gr.ImageEditor(
                type="pil",
                label="Draw Your Own Annotations",
                height=400
            )
            save_manual_btn = gr.Button("Save Manual Annotations")
            
            # Step 4: Generate Veo3
            gr.Markdown("### 4️⃣ Generate Veo3 JSON")
            user_prompt = gr.Textbox(
                label="Describe Your Video",
                placeholder="A sweeping cinematic shot that...",
                lines=3
            )
            generate_veo3_btn = gr.Button("Generate Veo3 JSON", variant="primary", size="lg")
            
            # Add a note about the video prompt
            gr.Markdown("**Note:** Make sure to describe your video above before clicking Generate!")
        
        # RIGHT COLUMN - Outputs
        with gr.Column(scale=2):
            # Status
            status = gr.Markdown("Ready to start")
            
            # Current Image Display
            current_image = gr.Image(label="Current Working Image", type="pil", height=400)
            
            # Image Gallery
            with gr.Accordion("📸 All Images", open=False):
                image_gallery = gr.Gallery(
                    label="Image History",
                    show_label=False,
                    elem_id="gallery",
                    columns=3,
                    rows=1,
                    object_fit="contain",
                    height="150px"
                )
            
            # Analysis Results
            with gr.Accordion("📊 Image Analysis", open=False):
                overview_display = gr.Markdown(label="Scene Overview")
                instructions_display = gr.Code(
                    language="json",
                    label="Annotation Instructions",
                    lines=10
                )
            
            # Veo3 Output
            veo3_output = gr.Code(
                language="json",
                label="Veo3 JSON Output",
                lines=20
            )
    
    # Wire up the interface
    def process_and_analyze(image_upload, gen_prompt, state):
        # Get image
        image, status_msg, state = generate_or_upload_image(image_upload, gen_prompt, state)
        if image is None:
            return None, status_msg, "", "", [], state
        
        # Analyze
        overview, instructions, analyze_status, state = analyze_for_annotations(image, state)
        
        # Update gallery
        gallery_images = update_gallery(state)
        
        # Update editor with current image
        return image, f"{status_msg} → {analyze_status}", overview, instructions, gallery_images, state
    
    def create_annotations(state):
        if state.original_image is None:
            return None, "❌ No image loaded", state.original_image, [], state
        
        annotated, status_msg, state = create_ai_annotations(state.original_image, state.annotation_instructions, state)
        gallery_images = update_gallery(state)
        if annotated:
            # Update editor with original image for manual annotations
            return annotated, status_msg, state.original_image, gallery_images, state
        else:
            return state.original_image, status_msg, state.original_image, gallery_images, state
    
    def update_editor_on_manual_save(editor_data, state):
        img, status_msg, state = save_manual_annotations(editor_data, state)
        gallery_images = update_gallery(state)
        return img, status_msg, gallery_images, state
    
    def switch_image(choice, state):
        """Switch between different image versions"""
        image = get_selected_image(choice, state)
        if image:
            return image, image  # Update both current_image and editor
        return None, None
    
    def update_gallery(state):
        """Update gallery with all available images"""
        images = []
        if state.original_image:
            images.append((state.original_image, "Original"))
        if state.ai_annotated_image:
            images.append((state.ai_annotated_image, "AI Annotated"))
        if state.manual_annotated_image:
            images.append((state.manual_annotated_image, "Manual Annotated"))
        return images
    
    # Connect buttons
    process_btn.click(
        process_and_analyze,
        inputs=[image_upload, gen_prompt, app_state],
        outputs=[current_image, status, overview_display, instructions_display, image_gallery, app_state]
    ).then(
        lambda img: img,
        inputs=[current_image],
        outputs=[image_editor]
    )
    
    ai_annotate_btn.click(
        create_annotations,
        inputs=[app_state],
        outputs=[current_image, status, image_editor, image_gallery, app_state]
    )
    
    save_manual_btn.click(
        update_editor_on_manual_save,
        inputs=[image_editor, app_state],
        outputs=[current_image, status, image_gallery, app_state]
    )
    
    image_choice.change(
        switch_image,
        inputs=[image_choice, app_state],
        outputs=[current_image, image_editor]
    )
    
    generate_veo3_btn.click(
        generate_veo3_json,
        inputs=[user_prompt, image_choice, app_state],
        outputs=[veo3_output, status]
    )

if __name__ == "__main__":
    app.launch(share=True)