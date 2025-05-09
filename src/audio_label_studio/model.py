from PIL import Image


class OCRModel:
    def __init__(self):
        print("[INFO] Initializing OCR model...")

    def predict(self, image: Image.Image):
        # 示例：返回 [(text, (x, y, width, height))]，单位为像素
        width, height = image.size
        return [
            ("Hello", (50, 40, 100, 30)),
            ("World", (60, 100, 120, 35))
        ]
