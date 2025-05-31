
from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("" ,tags=["recipes"])
def recipes_check():
    """
    レシピのチェックエンドポイント
    """
    return JSONResponse(content={"dish_name": "生姜焼き"})

@router.get("/{recipe_id}", tags=["recipes"])
def get_recipe_id(recipe_id: int):
    """
    レシピIDを受け取ってIDを返すエンドポイント
    """
    return JSONResponse(content={"recipe_id": recipe_id})