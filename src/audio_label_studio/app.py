from fastapi import FastAPI
from dotenv import load_dotenv
from .ocr_predict import router as ocr_router

load_dotenv('.env.prod')

app = FastAPI()
app.include_router(ocr_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
