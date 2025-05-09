from fastapi import FastAPI
from .ocr_predict import router as ocr_router

app = FastAPI()
app.include_router(ocr_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
