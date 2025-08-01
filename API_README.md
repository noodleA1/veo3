# Veo3 API Documentation

FastAPI endpoint for generating Veo3 video prompts from images.

## Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python veo3_api.py
```

The API will be available at `http://localhost:8000`

## Endpoints

### `POST /generate-veo3`

Generate a Veo3 JSON prompt from an image and text description.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `image` (file): Image file to analyze
  - `prompt` (string): Text description of desired video

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/generate-veo3" \
  -F "image=@/path/to/your/image.jpg" \
  -F "prompt=Create a cinematic shot with slow camera movement"
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/generate-veo3"
files = {"image": open("image.jpg", "rb")}
data = {"prompt": "Create a cinematic shot with slow camera movement"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "veo3_prompt": {
    "prompt": "Main video generation prompt",
    "scene_description": "Detailed scene description",
    "camera": {
      "initial_position": "Starting position",
      "movement": "Camera movement description",
      "focal_length": "24mm",
      "depth_of_field": "Shallow",
      "stabilization": "Smooth"
    },
    "subject_motion": {
      "primary": "Main subject movement",
      "path": "Movement path",
      "secondary_elements": "Other elements"
    },
    "visual_style": {
      "treatment": "Cinematic",
      "color_grading": "Warm tones",
      "lighting": "Natural"
    },
    "timing": {
      "duration_seconds": 8,
      "pacing": "Slow",
      "key_moments": "2s, 5s marks"
    },
    "technical_specs": {
      "aspect_ratio": "16:9",
      "resolution": "4K",
      "frame_rate": "24fps",
      "motion_blur": "Natural"
    },
    "audio_hints": {
      "ambience": "Nature sounds",
      "music_style": "Orchestral",
      "sound_effects": ["wind", "footsteps"]
    }
  },
  "scene_analysis": {
    "description": "Scene overview",
    "main_subject": "Primary focus",
    "mood": "Serene",
    "lighting": "Golden hour"
  },
  "annotation_applied": true
}
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Error Responses

- `400 Bad Request`: Invalid image file
- `422 Unprocessable Entity`: Missing required parameters
- `500 Internal Server Error`: Processing error with details

## Rate Limiting

Currently no rate limiting is implemented. Consider adding for production use.

## Authentication

Currently no authentication is required. Add API keys for production deployment.