from fastapi import APIRouter
from backend.database import db


router = APIRouter()

# Import and include other route modules here
from backend.routes.recommendations import router as recommendations_router
router.include_router(recommendations_router)
