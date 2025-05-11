from fastapi.routing import APIRouter
from fastapi import Request
from typing import List
from PIL import Image
import io
import uuid
import json
import requests
from .model import OCRModel, TesseractOCRModel
import os

router = APIRouter(prefix="/ocr")
ocr_model = TesseractOCRModel()


def download_image(task: dict):
    image_url = task["data"].get("ocr")
    if not image_url:
        return None
    image_url = f"http://localhost:8080{image_url}"
    headers = {
        "Authorization": f"Token {os.getenv('LABEL_STUDIO_API_TOKEN')}"
    }
    response = requests.get(image_url, headers=headers)
    if response.status_code != 200:
        return None
    return response.content


def process_ocr_results(ocr_results, img_width: int, img_height: int):
    """
    处理OCR结果，转换为Label Studio标注格式

    Args:
        ocr_results: OCR识别结果，格式为[(text, (x, y, w, h)), ...]
        img_width: 图片宽度
        img_height: 图片高度

    Returns:
        list: Label Studio标注结果列表
    """
    result = []
    for text, (x, y, w, h) in ocr_results:
        # 生成唯一ID，用于关联矩形框和文本
        id = uuid.uuid4().hex[:8]

        # 转换为百分比坐标
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

    return result


def download_as_image_object(task: dict):
    image_content = download_image(task)
    if not image_content:
        return None
    return Image.open(io.BytesIO(image_content))


def prelabeling(task: dict):
    img = download_as_image_object(task)
    if not img:
        return {"result": [], "score": 0.0}

    img_width, img_height = img.size
    ocr_results = ocr_model.predict(img)
    result = process_ocr_results(ocr_results, img_width, img_height)
    return {
        "result": result,
        "score": 0.95
    }


def process_ocr_detect_result(ocr_result: list, bbox_label: dict):
    result = []
    uid = bbox_label['id']
    x = bbox_label['value']['x']
    y = bbox_label['value']['y']
    w = bbox_label['value']['width']
    h = bbox_label['value']['height']
    result.append(
        {
            "id": uid,
            "from_name": "label",
            "to_name": "image",
            "type": "rectanglelabels",
            "value": {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "rotation": 0,
                    "labels": ["Text"]
            }
        }
    )
    text = "".join([text for text, _ in ocr_result])
    print(text)
    result.append({
        "id": uid,
        "from_name": "transcription",
        "to_name": "image",
        "type": "textarea",
        "value": {
            "text": [text],
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "rotation": 0
        }
    })
    return result


def auto_detect(task: dict, bbox_label: dict):
    img = download_as_image_object(task)
    if not img:
        return {"result": [], "score": 0.0}

    img_width, img_height = img.size

    x = bbox_label['value']['x'] / 100 * img_width
    y = bbox_label['value']['y'] / 100 * img_height
    w = bbox_label['value']['width'] / 100 * img_width
    h = bbox_label['value']['height'] / 100 * img_height

    print(x, y, w, h)
    img_crop = img.crop((int(x), int(y), int(x + w), int(y + h)))

    ocr_results = ocr_model.predict(img_crop)
    result = process_ocr_detect_result(ocr_results, bbox_label)

    return {
        "result": result,
        "score": 0.95
    }


def handle_tasks(tasks: List[dict]):
    results = []
    for task in tasks:
        results.append(prelabeling(task))
    return results


def handle_detect(tasks: List[dict], bbox_label: dict):
    results = []
    for task in tasks:
        results.append(auto_detect(task, bbox_label))
    return results


@router.post("/predict")
async def predict(request: Request):
    data: dict = await request.json()
    if "params" not in data or data['params']['context'] is None:
        tasks: List[dict] = data["tasks"]
        results = handle_tasks(tasks)
    else:
        tasks: List[dict] = data["tasks"]
        bbox_labels: List[dict] = data['params']['context']['result'][0]
        print(bbox_labels)
        results = handle_detect(tasks, bbox_labels)
    return {
        "results": results
    }


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/setup")
async def setup():
    return {"status": "ok", "model_version": "1.0.0"}


@router.post("/webhook")
async def webhook(request: Request):
    data: dict = await request.json()
    return {"status": "ok"}
