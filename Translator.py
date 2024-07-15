import sys
import requests
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QVBoxLayout, QWidget, QLabel, QTextEdit, QHBoxLayout, QSpinBox
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPainter, QPen
import numpy as np
import torch
from paddleocr import PaddleOCR
from PIL import Image
import mss
import ctypes
import os
import ollama

# Global variables
# OLLAMA_API_URL = "http://localhost:11434"
CAPTURE_INTERVAL = 250  # milliseconds

class TransparentOverlay(QWidget):
    selection_made = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(QGuiApplication.primaryScreen().geometry())
        self.begin = QPoint()
        self.end = QPoint()
        self.selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if self.selecting:
            selected_rect = QRect(self.begin, self.end).normalized()
            painter.fillRect(selected_rect, Qt.GlobalColor.transparent)
            painter.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine))
            painter.drawRect(selected_rect)

    def mousePressEvent(self, event):
        self.begin = event.position().toPoint()
        self.end = self.begin
        self.selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        self.selecting = False
        self.hide()
        selected_rect = QRect(self.begin, self.end).normalized()
        self.selection_made.emit(selected_rect)

    def showEvent(self, event):
        self.begin = QPoint()
        self.end = QPoint()
        self.selecting = False
        self.update()

class TranslationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # Prevents the window from stealing focus
        self.layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 5px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 30px;
            }
        """)
        self.layout.addWidget(self.text_edit)
        self.setLayout(self.layout)
        self.dragging = False
        self.offset = QPoint()

    def setText(self, text):
        self.text_edit.setText(text)
        self.raise_()  # Ensures the window stays on top after updating text

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.position().toPoint() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

class TranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gpu_available = torch.cuda.is_available()
        print(f"GPU acceleration is {'available' if self.gpu_available else 'not available'}")
        
        self.initUI()
        self.selected_area = None
        self.previous_text = ""
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.capture_and_translate)
        self.overlay = TransparentOverlay()
        self.overlay.selection_made.connect(self.on_area_selected)
        self.translation_window = TranslationWindow()
        
        os.environ['KMP_DUPLICATE_LIB_OK']='True'
        
        # Initialize PaddleOCR reader
        self.paddleocr_reader = None
        self.update_reader(self.source_language_combo.currentText())

        self.sct = mss.mss()
        self.scaling_factor = self.get_scaling_factor()
        print(f"Display scaling factor: {self.scaling_factor}")
        
    def get_scaling_factor(self):
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return user32.GetDpiForSystem() / 96.0

    def initUI(self):
        self.setWindowTitle('Real-time Translator')
        self.setGeometry(0, 0, 300, 200)

        layout = QVBoxLayout()

        self.choose_area_btn = QPushButton('Choose Area', self)
        self.choose_area_btn.clicked.connect(self.start_area_selection)
        layout.addWidget(self.choose_area_btn)

        # Scale factor input
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel('Scale Factor (%):'))
        self.scale_factor_input = QSpinBox()
        self.scale_factor_input.setRange(100, 300)
        self.scale_factor_input.setValue(150)
        self.scale_factor_input.setSingleStep(10)
        scale_layout.addWidget(self.scale_factor_input)
        layout.addLayout(scale_layout)

        self.source_language_combo = QComboBox(self)
        self.source_language_combo.addItems(['English', 'Japanese'])
        self.source_language_combo.currentTextChanged.connect(self.update_reader)
        layout.addWidget(QLabel('Source Language:'))
        layout.addWidget(self.source_language_combo)

        self.target_language_combo = QComboBox(self)
        self.target_language_combo.addItems(['Traditional Chinese', 'English'])
        layout.addWidget(QLabel('Target Language:'))
        layout.addWidget(self.target_language_combo)

        self.model_combo = QComboBox(self)
        self.update_model_list()
        layout.addWidget(QLabel('Translation Model:'))
        layout.addWidget(self.model_combo)

        self.show_translation_btn = QPushButton('Show Translation', self)
        self.show_translation_btn.clicked.connect(self.toggle_translation)
        layout.addWidget(self.show_translation_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_reader(self, language):
        if language == 'English':
            self.paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True, show_log=False)
        elif language == 'Japanese':
            self.paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=True, show_log=False)
        print(f"PaddleOCR reader updated for {language}")

    def update_model_list(self):
        try:
            models = ollama.list()
            model_names = [model['name'] for model in models['models']]
            self.model_combo.clear()
            self.model_combo.addItems(model_names)
            default_model = "gemma2:latest"
            if default_model in model_names:
                self.model_combo.setCurrentText(default_model)
            else:
                self.model_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"Error fetching model list: {e}")
            self.model_combo.clear()
            self.model_combo.addItem("gemma2:latest")

    def start_area_selection(self):
        self.overlay.show()

    def on_area_selected(self, rect):
        scale_factor = self.scale_factor_input.value() / 100.0
        physical_rect = QRect(
            int(rect.left() * scale_factor),
            int(rect.top() * scale_factor),
            int(rect.width() * scale_factor),
            int(rect.height() * scale_factor)
        )
        self.selected_area = {
            "top": physical_rect.top(),
            "left": physical_rect.left(),
            "width": physical_rect.width(),
            "height": physical_rect.height()
        }
        self.choose_area_btn.setText(f"Selected Area: {physical_rect.width()}x{physical_rect.height()}")
        
        # Set translation window size and position
        translation_width = int(physical_rect.width() * 0.9 / scale_factor)  # 90% of the selected area width
        translation_height = 200
        translation_x = int((physical_rect.left() + physical_rect.width() / 2) / scale_factor - translation_width / 2)
        translation_y = int(physical_rect.bottom() / scale_factor + 10)  # Initial position below the selected area

        # Get the screen size
        screen = QApplication.primaryScreen().geometry()

        # Check if the translation window goes beyond the screen bottom
        if translation_y + translation_height > screen.height():
            # If it does, place it above the selected area instead
            translation_y = int(physical_rect.top() / scale_factor - translation_height - 10)

        # Ensure the window is not positioned off the top of the screen
        translation_y = max(0, translation_y)

        # Ensure the window is not positioned off the sides of the screen
        translation_x = max(0, min(translation_x, screen.width() - translation_width))

        self.translation_window.setGeometry(translation_x, translation_y, translation_width, translation_height)

    def capture_and_translate(self):
        if self.selected_area:
            try:
                screenshot = self.sct.grab(self.selected_area)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_np = np.array(img)
                
                result = self.paddleocr_reader.ocr(img_np, cls=True)
                text = ' '.join([line[1][0] for line in result[0]]) if result and result[0] else ""
                # print(f"Extracted text: {text}")
                if text and text != self.previous_text:
                    self.previous_text = text
                    translated_text = self.translate_text(text)
                    self.translation_window.setText(translated_text)
                # elif not text:
                #     print("No text detected in the image")
                #     self.translation_window.setText("No text detected")
                # else:
                #     print("No new text detected")
            except Exception as e:
                print(f"Error in capture_and_translate: {e}")
                self.translation_window.setText(f"Error: {str(e)}")

    def toggle_translation(self):
        if self.capture_timer.isActive():
            self.capture_timer.stop()
            self.show_translation_btn.setText('Show Translation')
            self.translation_window.hide()
        else:
            if self.selected_area:
                self.capture_timer.start(200)  # Capture every 200ms
                self.show_translation_btn.setText('Stop Translation')
                self.translation_window.show()
            else:
                print("Please select an area first")

    def translate_text(self, text):
        target_language = self.target_language_combo.currentText()
        
        start_time = time.time()
        
        result = self.translate_text_ollama_lib(text, target_language)
        
        end_time = time.time()
        translation_time = end_time - start_time
        
        print(f"Origin: {text}\nTranslated: {result}\nTranslation time: {translation_time:.2f} seconds")
        
        return result
        
    def translate_text_ollama_lib(self, text, target_language):
        model = self.model_combo.currentText()
        
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following {self.source_language_combo.currentText()} text to {target_language}. Maintain accuracy and natural phrasing. Only return the translated text, without any additional explanation or commentary."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_ctx": 1024
                }
            )
            
            return response['message']['content']
        except Exception as e:
            print(f"Error in Ollama API request: {e}")
            return f"Translation failed. Error: {str(e)}"
    
def main():
    app = QApplication(sys.argv)
    translator = TranslatorApp()
    translator.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()