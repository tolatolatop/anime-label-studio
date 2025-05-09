from fastapi.routing import APIRouter
from fastapi import Request
from typing import List
from PIL import Image
import io
import uuid
import requests
from .model import OCRModel
import os

router = APIRouter(prefix="/ocr")
ocr_model = OCRModel()


@router.post("/predict")
async def predict(request: Request):
    data: dict = await request.json()
    tasks: List[dict] = data["tasks"]
    results = []

    for task in tasks:
        image_url = task["data"].get("ocr")
        if not image_url:
            results.append({"result": [], "score": 0.0})
            continue

        image_url = f"http://localhost:8080{image_url}"

        headers = {
            "Authorization": f"Token {os.getenv('LABEL_STUDIO_API_TOKEN')}"
        }

        response = requests.get(image_url, headers=headers)
        if response.status_code != 200:
            print(response.text)
            print("图片请求失败，状态码：", response.status_code)
            results.append({"result": [], "score": 0.0})
            continue
        if not response.headers.get("Content-Type", "").startswith("image/"):
            print("返回内容不是图片，实际Content-Type:",
                  response.headers.get("Content-Type"))
            results.append({"result": [], "score": 0.0})
            continue

        try:
            img = Image.open(io.BytesIO(response.content))
        except Exception as e:
            print("图片解码失败:", e)
            results.append({"result": [], "score": 0.0})
            continue
        img_width, img_height = img.size

        ocr_results = ocr_model.predict(img)
        print(ocr_results)

        result = []
        for text, (x, y, w, h) in ocr_results:
            # 转换为百分比坐标
            id = uuid.uuid4().hex[:8]
            x_pct = x / img_width * 100
            y_pct = y / img_height * 100
            w_pct = w / img_width * 100
            h_pct = h / img_height * 100

            # 标注框
            result.append({
                "id": id,
                "from_name": "label",
                "to_name": "image",
                "type": "rectanglelabels",
                "value": {
                    "x": x_pct,
                    "y": y_pct,
                    "width": w_pct,
                    "height": h_pct,
                    "rotation": 0,
                    "labels": ["Text"]
                }
            })

            # 文本标注
            result.append({
                "id": id,
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
    return {
        "results": results
    }


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/setup")
async def setup():
    return {"status": "ok", "model_version": "1.0.0"}
