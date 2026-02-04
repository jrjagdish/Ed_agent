import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile,HTTPException
import pdfplumber
from app import start_process

load_dotenv()

app = FastAPI()

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB



def get_text_from_pdf(file:UploadFile):
    file.file.seek(0)
    with pdfplumber.open(file.file) as pdf:
        if len(pdf.pages) > 3:
            return {"ERROR: Please provide the pdf which has less than 3 pages"}
        else:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

    if not text.strip():
        return {"ERROR : No data to extract"}

    return text            

@app.post("/upload")
async def upload_file(file: UploadFile):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    
    data = get_text_from_pdf(file)
    if isinstance(data, dict) and "error" in data:
        return data
    

    result = await start_process({"input_text":data})
    file.file.seek(0)

    upload_result = cloudinary.uploader.upload(
        file.file,
        resource_type = "raw",
        folder = "pdfs",
        public_id = file.filename
    )
    message="Successful!"

    return {"Message":message,
            "Secure_url": upload_result['secure_url'],
            "Summary":result.get("Summary"),
            "MCQs":result.get("MCQs"),
            "Token Cost" : f"{result.get("Estimated Cost")}$"
            }    
