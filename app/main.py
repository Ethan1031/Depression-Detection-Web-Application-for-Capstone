from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.api import router

app = FastAPI()

# Include API endpoints
app.include_router(router)

# Serve frontend HTML page
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# run by using uvicorn app.main:app --reload
