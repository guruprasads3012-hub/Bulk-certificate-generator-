from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

app = FastAPI(title="Bulk Certificate Generator API")

@app.get("/")
def read_root():
    return {"message": "Bulk Certificate Generator API is running"}

@app.post("/generate")
async def generate_certificates(file: UploadFile = File(...)):
    # 1. Check if the file is a CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    
    try:
        # 2. Read the CSV
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Make sure there is a 'Name' column
        if 'Name' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain a 'Name' column")

        # 3. Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            # Loop through each name in the CSV
            for index, row in df.iterrows():
                name = str(row['Name'])
                
                # Create a simple certificate image
                img = Image.new('RGB', (800, 600), color='white')
                d = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except IOError:
                    font = ImageFont.load_default()
                
                d.text((200, 250), f"Certificate of Completion", fill='black', font=font)
                d.text((300, 350), f"Presented to: {name}", fill='black', font=font)
                
                # Save the image as a PDF in memory
                pdf_buffer = io.BytesIO()
                img.save(pdf_buffer, format="PDF")
                pdf_buffer.seek(0)
                
                # Add the PDF to the ZIP file
                zip_file.writestr(f"{name}_certificate.pdf", pdf_buffer.read())

        zip_buffer.seek(0)
        
        # 4. Return the ZIP file
        return StreamingResponse(
            zip_buffer, 
            media_type="application/zip", 
            headers={"Content-Disposition": "attachment; filename=certificates.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
