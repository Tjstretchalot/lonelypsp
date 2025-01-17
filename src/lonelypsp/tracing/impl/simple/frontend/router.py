from fastapi import APIRouter


router = APIRouter()


@router.get("/index.html")
def index():
    return "Hello, World!"
