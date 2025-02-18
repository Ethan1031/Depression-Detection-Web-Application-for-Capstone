from fastapi import FastAPI, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from .call import predict_api
import os

app = FastAPI(title="EEG Depression Detection")

# Serve frontend HTML page
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Handle EEG file upload and return prediction"""
    if not file.filename.endswith('.edf'):
        return {"error": "Please upload an EDF file"}
    
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Get prediction
        result = predict_api(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return result
    
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# run by using uvicorn app.main:app --reload
