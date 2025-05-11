from PIL import Image
import pytesseract
import numpy as np
import os


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


class TesseractOCRModel(OCRModel):
    def __init__(self, lang='jpn+eng'):
        """
        初始化 Tesseract OCR 模型

        Args:
            lang: OCR语言，默认支持日语和英语
        """
        super().__init__()
        self.lang = lang
        # 测试 Tesseract 是否可用
        try:
            pytesseract.get_tesseract_version()
            print("[INFO] Tesseract OCR initialized successfully.")
        except Exception as e:
            print("[ERROR] Failed to initialize Tesseract OCR:", e)
            print(
                "[ERROR] Please make sure Tesseract is installed and properly configured.")
            raise

    def predict(self, image: Image.Image):
        """
        使用 Tesseract 进行 OCR 识别

        Args:
            image: PIL Image对象

        Returns:
            list: [(text, (x, y, width, height)), ...] 格式的识别结果
        """
        # 获取详细的OCR结果，包括边界框
        result = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT
        )

        ocr_results = []
        n_boxes = len(result['text'])

        for i in range(n_boxes):
            # 过滤掉空文本和置信度低的结果
            if int(result['conf'][i]) > 60 and result['text'][i].strip():
                x = result['left'][i]
                y = result['top'][i]
                w = result['width'][i]
                h = result['height'][i]
                text = result['text'][i]

                ocr_results.append((text, (x, y, w, h)))

        return ocr_results
