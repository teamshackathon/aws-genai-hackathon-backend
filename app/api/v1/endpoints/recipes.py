
from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("" ,tags=["recipes"])
def recipes_check():
    """
    レシピのチェックエンドポイント
    """
    return JSONResponse(content={"dish_name": "生姜焼き"})
