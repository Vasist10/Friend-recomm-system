from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import recommendations  # Ensure routes directory has an __init__.py file
import uvicorn
from backend.database import get_db

app = FastAPI(title="Friend Recommendation System")

@app.get("/test_db")
def test_db_connection():
    """Check if the database connection is working."""
    db = get_db()
    try:
        query = "MATCH (n) RETURN COUNT(n) AS node_count"  # Count total nodes in DB
        result = db.run_query(query).single()
        return {"message": "Connected successfully!", "total_nodes": result["node_count"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")



# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(recommendations.router)

@app.get("/")
def home():
    return {"message": "Friend Recommendation System API is running"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)  # Correct import path
