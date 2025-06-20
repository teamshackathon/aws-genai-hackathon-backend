from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import Users
from app.schemas.shopping import Shopping, ShoppingCreate, ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate, ShoppingList
from app.services.recipe_service import RecipeService
from app.services.shopping_service import ShoppingService

router = APIRouter()

def get_shopping_service(db: Session = Depends(deps.get_db)) -> ShoppingService:
    try:
        return ShoppingService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ショッピングサービスの初期化に失敗しました: {str(e)}"
        )
    
def get_recipe_service(db: Session = Depends(deps.get_db)) -> RecipeService:
    try:
        return RecipeService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"レシピサービスの初期化に失敗しました: {str(e)}"
        )

# 1. 買い物リスト一覧取得（ページネーション対応）
@router.get("", response_model=ShoppingList)
def get_shopping_lists(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりのリスト数"),
    keyword: Optional[str] = Query(None, description="検索キーワード"),
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.get_lists_with_pagination(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        keyword=keyword
    )

# 2. 買い物リスト作成
@router.post("", response_model=Shopping)
def create_shopping_list(
    req: ShoppingCreate,
    recipe_service: RecipeService = Depends(get_recipe_service),
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    # 対象のレシピが存在するか確認
    recipe = recipe_service.get_recipe_by_id(req.recipe_id, user_id=current_user.id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    shopping = shopping_service.create_list(
        recipe_id=req.recipe_id,
        list_name=f"{recipe.recipe_name}の買い物リスト",
    )
    if not shopping:
        raise HTTPException(status_code=400, detail="Failed to create shopping list")
    # ユーザーショッピングを作成
    user_shopping = shopping_service.create_user_shopping(
        shopping_id=shopping.id,
        user_id=current_user.id,
    )
    if not user_shopping:
        raise HTTPException(status_code=400, detail="Failed to create user shopping")
    
    ingridients = recipe_service.get_ingredient_by_recipe_id(req.recipe_id)
    if not ingridients:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # shopiingItemようにingridientsを整形
    shopping_items = [  
        ShoppingItemCreate(
            shopping_id=shopping.id,
            ingredient=ingredient.ingredient,
            amount=ingredient.amount,
            is_checked=False,
            created_date=ingredient.created_date.isoformat(),
            updated_date=ingredient.updated_date.isoformat()
        ) for ingredient in ingridients
    ]
    # 買い物リストにアイテムを追加
    shopping_items = shopping_service.create_items(
        items=shopping_items,
    )
    if not shopping_items:
        raise HTTPException(status_code=400, detail="Failed to create shopping items")  
    return shopping

# 3. 買い物リスト詳細取得
@router.get("/{shopping_id}", response_model=Shopping)
def get_shopping_list_detail(
    shopping_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.get_shopping(shopping_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return result

# 4. 買い物リストのアイテム一覧取得
@router.get("/{shopping_id}/items", response_model=List[ShoppingItem])
def get_shopping_list_items(
    shopping_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.get_items(shopping_id)

# 5. 買い物リストアイテムの更新
@router.put("/item/{shopping_item_id}", response_model=ShoppingItem)
def update_shopping_item(
    shopping_item_id: int,
    req: ShoppingItemUpdate,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.update_item(shopping_item_id, req)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
