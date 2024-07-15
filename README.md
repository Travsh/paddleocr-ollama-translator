# Real-time Translator

A desktop application that provides real-time translation of selected screen areas using OCR technology and AI-powered translation.

![Application Screenshot](/demo_images/gui.png)

![Full Screen Application](/demo_images/fullscreen.png)

## Features

- Real-time screen capture and translation
- Support for multiple languages (English, Japanese, Traditional Chinese)
- Customizable translation area selection
- Movable and resizable translation overlay
- Integration with Ollama for AI-powered translation
- Adjustable screen scaling factor
- GPU acceleration support for OCR (when available)

## Demo

[Watch the demo video](/demo_images/demo.mp4)

## Requirements

- Python 3.9.19
- PyQt6
- PaddleOCR
- Ollama
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone this repository:

git clone https://github.com/Travsh/paddleocr-ollama-translator.git
cd paddleocr-ollama-translator

2. Install the required Python packages:

pip install -r requirements.txt

3. Ensure Ollama is installed and running on your system. You can download it from [https://ollama.ai/](https://ollama.ai/)

## Usage

1. Start the application:

python Translator.py

2. Select the source language (English or Japanese) from the dropdown menu.

3. Choose the target language for translation (Traditional Chinese or English).

4. Adjust the scale factor if necessary (default is 150%).

5. Click "Choose Area" and select the screen area you want to translate.

6. Click "Show Translation" to start the real-time translation.

7. The translated text will appear in a movable overlay window near the selected area.

8. You can drag the translation window to reposition it as needed.

## Configuration

- **Scale Factor**: Adjust this if your display scaling is different from the default (150%).
- **Translation Model**: Select the Ollama model you want to use for translation. (Recommended: "gemma2")

## Troubleshooting

If you encounter any issues:

1. Ensure Ollama is running and accessible at `http://localhost:11434`.
2. Check that all required Python packages are installed correctly.
3. Verify that your selected Ollama model supports the languages you're translating between.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Ollama](https://ollama.ai/) for providing the AI translation capabilities.
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for OCR functionality.
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework.