# Veo3 Enhanced Prompt Generator

A streamlined application for creating AI-powered video generation prompts with visual storyboard annotations. Available as both a Gradio UI and FastAPI endpoint.

## Features

- **Image Input**: Upload existing images or generate new ones with AI
- **Intelligent Analysis**: Automatic scene analysis and storyboard annotation suggestions using Google Gemini
- **AI Annotations**: Generate professional storyboard markings using Flux Kontext
- **Manual Annotations**: Add your own custom markings and annotations
- **Flexible Workflow**: Choose between original, AI-annotated, or manually annotated images
- **Veo3 JSON Generation**: Create comprehensive video generation specifications
- **API Endpoint**: Programmatic access via FastAPI

## Prerequisites

- Python 3.8+
- Google Gemini API key
- Replicate API token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/noodleA1/veo3.git
cd veo3
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
REPLICATE_API_TOKEN=your_replicate_token_here
```

## Usage

### Option 1: Gradio UI

Run the interactive web interface:
```bash
python veo3_complete.py
```

The app will launch in your browser with a user-friendly interface.

#### Workflow:
1. **Start with an Image**: Upload an existing image or generate one using AI
2. **Analyze**: The system automatically analyzes the image for storyboard opportunities
3. **Create Annotations**: Generate AI annotations or add your own manual markings
4. **Choose Working Image**: Select which version to use (original, AI-annotated, or manual)
5. **Generate Veo3 JSON**: Describe your video vision and generate the final specification

### Option 2: FastAPI Endpoint

Run the API server:
```bash
python veo3_api.py
```

The API will be available at `http://localhost:8000`

#### API Usage:

**Endpoint:** `POST /generate-veo3`

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/generate-veo3" \
  -F "image=@/path/to/your/image.jpg" \
  -F "prompt=Create a cinematic shot with slow camera movement"
```

**Example with Python:**
```python
import requests

url = "http://localhost:8000/generate-veo3"
files = {"image": open("image.jpg", "rb")}
data = {"prompt": "Create a cinematic shot with slow camera movement"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Interactive API docs:** Visit `http://localhost:8000/docs`

## Annotation Color Coding

- **RED**: Primary subject/hero element movements
- **BLUE**: Camera motion indicators
- **GREEN**: Secondary elements and focal points
- **ORANGE**: Timing and scene information

## Project Structure

```
veo3/
├── veo3_complete.py      # Gradio UI application
├── veo3_api.py          # FastAPI endpoint
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this)
├── README.md            # This file
└── veo3_json_examples.json  # Example output structures
```

## Response Format

The Veo3 JSON output includes:
- Main video generation prompt
- Scene description with annotated elements
- Camera settings and movements
- Subject motion paths
- Visual style and treatment
- Timing and pacing
- Technical specifications
- Audio hints
- Storyboard integration instructions

## Technologies Used

- **Gradio**: Web interface for UI version
- **FastAPI**: REST API framework
- **Google Gemini 1.5 Pro**: Image analysis and vision understanding
- **Replicate Flux**: Image generation and annotation
- **Pillow**: Image processing

## Deployment

### Gradio App
- Can be deployed to Hugging Face Spaces
- Or any server with Python support

### FastAPI
- Deploy to any cloud provider (AWS, GCP, Azure)
- Docker-ready for containerized deployment
- Supports horizontal scaling

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.