from dotenv import load_dotenv
import os
import pytesseract

load_dotenv('.env.prod')

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")
