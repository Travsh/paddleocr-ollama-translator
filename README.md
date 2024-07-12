# Real-time Translator

A desktop application that provides real-time translation of selected screen areas using OCR technology and AI-powered translation.

![Application GUI](/demo_images/gui.png)

## Features

- Real-time screen capture and translation
- Support for multiple OCR engines (PaddleOCR and EasyOCR)
- Integration with Ollama for AI-powered translation
- Adjustable screen scaling factor
- Movable and resizable translation overlay
- Support for English and Japanese OCR
- Translation to Traditional Chinese and English

## Requirements

- Python 3.9
- Ollama: This application requires Ollama to be installed and running. You can download and install Ollama from [https://ollama.com/](https://ollama.com/)
- Other Python dependencies are listed in `requirements.txt`

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/real-time-translator.git
   cd real-time-translator
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure Ollama is installed and running on your system.

## Usage

1. Start the application:
   ```
   python Translator.py
   ```

2. Select the source language (English or Japanese) and target language (Traditional Chinese or English).

3. Choose the OCR method (PaddleOCR or EasyOCR).

4. Click "Choose Area" and select the screen area you want to translate.

5. Click "Show Translation" to start the real-time translation.

![Translation in action](/demo_images/fullscreen.png)

6. The translated text will appear in a movable overlay window.

## Configuration

- **Scale Factor**: Adjust this if your display scaling is different from the default (150%).
- **OCR Method**: Choose between PaddleOCR (default) and EasyOCR based on your preference and performance needs.
- **Translation Model**: Select the Ollama model you want to use for translation.

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

- [Ollama](https://ollama.com/) for providing the AI translation capabilities.
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) and [EasyOCR](https://github.com/JaidedAI/EasyOCR) for OCR functionality.
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework.