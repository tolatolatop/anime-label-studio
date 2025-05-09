from fastapi.routing import APIRouter
from fastapi import Request
from typing import List
from PIL import Image
import io
import requests
from .model import OCRModel

router = APIRouter(prefix="/ocr")
ocr_model = OCRModel()


@router.post("/predict")
async def predict(request: Request):
    tasks: List[dict] = await request.json()
    results = []

    for task in tasks:
        image_url = task["data"].get("image")
        if not image_url:
            results.append({"result": [], "score": 0.0})
            continue

        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        img_width, img_height = img.size

        ocr_results = ocr_model.predict(img)

        result = []
        for text, (x, y, w, h) in ocr_results:
            # 转换为百分比坐标
            x_pct = x / img_width * 100
            y_pct = y / img_height * 100
            w_pct = w / img_width * 100
            h_pct = h / img_height * 100

            # 标注框
            result.append({
                "from_name": "label",
                "to_name": "image",
                "type": "rectanglelabels",
                "value": {
                    "x": x_pct,
                    "y": y_pct,
                    "width": w_pct,
                    "height": h_pct,
                    "rotation": 0,
                    "labels": ["text"]
                }
            })

            # 文本标注
            result.append({
                "from_name": "transcription",
                "to_name": "image",
                "type": "textarea",
                "value": {
                    "text": [text],
                    "x": x_pct,
                    "y": y_pct,
                    "width": w_pct,
                    "height": h_pct,
                    "rotation": 0
                }
            })

        results.append({
            "result": result,
            "score": 0.95
        })

    return results
