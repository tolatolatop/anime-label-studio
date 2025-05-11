import base64
import io
import os
from PIL import Image
from dotenv import load_dotenv
from volcengine.visual.VisualService import VisualService


_visual_service = None


def get_visual_service():
    global _visual_service
    if _visual_service is None:
        _visual_service = VisualService()
        _visual_service.set_ak(os.getenv('VOLC_ACCESS_KEY'))
        _visual_service.set_sk(os.getenv('VOLC_SECRET_KEY'))

    return _visual_service


def image_to_base64(image: Image.Image):
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    return image_base64


def predict(image: Image.Image):
    form = dict()

    action = "MultiLanguageOCR"
    version = "2022-08-31"
    visual_service = get_visual_service()
    visual_service.set_api_info(action, version)

    form = dict()
    form["image_base64"] = image_to_base64(image)
    resp = visual_service.ocr_api(action, form)
    return resp


if __name__ == "__main__":
    load_dotenv('.env.prod')
    image = Image.open("test.png")
    data = predict(image)
    print(data)
