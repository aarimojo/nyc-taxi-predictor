from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.predictions import router as predict_router  # Correct import



app = FastAPI(
    title="Taxi Trip Predictor API",
    description="API for predicting taxi trip duration and fare",
    version="1.0.0"
)

app.include_router(predict_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "NYC Taxi Predictor API", 
        "endpoints": {
            "predict": "/predict (POST)"
        }
    }


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)