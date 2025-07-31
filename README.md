# Veo3 Enhanced Prompt Generator

A streamlined application for creating AI-powered video generation prompts with visual storyboard annotations.

## Features

- **Image Input**: Upload existing images or generate new ones with AI
- **Intelligent Analysis**: Automatic scene analysis and storyboard annotation suggestions using Google Gemini
- **AI Annotations**: Generate professional storyboard markings using Flux Kontext
- **Manual Annotations**: Add your own custom markings and annotations
- **Flexible Workflow**: Choose between original, AI-annotated, or manually annotated images
- **Veo3 JSON Generation**: Create comprehensive video generation specifications

## Prerequisites

- Python 3.8+
- Google Gemini API key
- Replicate API token

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd prompt-maker
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

Run the application:
```bash
python veo3_complete.py
```

The app will launch in your browser with a Gradio interface.

### Workflow

1. **Start with an Image**: Upload an existing image or generate one using AI
2. **Analyze**: The system automatically analyzes the image for storyboard opportunities
3. **Create Annotations**: Generate AI annotations or add your own manual markings
4. **Choose Working Image**: Select which version to use (original, AI-annotated, or manual)
5. **Generate Veo3 JSON**: Describe your video vision and generate the final specification

### Annotation Color Coding

- **RED**: Primary subject/hero element movements
- **BLUE**: Camera motion indicators
- **GREEN**: Secondary elements and focal points
- **ORANGE**: Timing and scene information

## Project Structure

```
prompt-maker/
├── veo3_complete.py      # Main application
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this)
├── backup/              # Legacy code archive
└── old_versions/        # Previous iterations
```

## Technologies Used

- **Gradio**: Web interface
- **Google Gemini 1.5 Pro**: Image analysis and vision understanding
- **Replicate Flux**: Image generation and annotation
- **Pillow**: Image processing

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.