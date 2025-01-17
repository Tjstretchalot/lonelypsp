from fastapi import APIRouter

router = APIRouter()


@router.get("/index.html")
def index() -> str:
    return "Hello, World!"
