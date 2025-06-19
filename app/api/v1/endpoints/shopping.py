from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.shopping import ShoppingItem
from app.models.user import Users
from app.schemas.shopping import ShoppingListCreateRequest, ShoppingListItemResponse, ShoppingListListResponse, ShoppingListResponse, UpdateShoppingListItemRequest
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
@router.get("", response_model=ShoppingListListResponse)
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
@router.post("", response_model=ShoppingListResponse)
def create_shopping_list(
    req: ShoppingListCreateRequest,
    recipe_service: RecipeService = Depends(get_recipe_service),
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.create_list(req, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create shopping list")
    ingridients = recipe_service.get_ingredient_by_recipe_id(req.recipe_id)
    if not ingridients:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # shopiingItemようにingridientsを整形
    shopping_items = [  
        ShoppingItem(
            user_shopping_id=result.id,
            ingredient_id=ingredient.id,
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
    return result

# 3. 買い物リスト詳細取得
@router.get("/{shopping_list_id}", response_model=ShoppingListResponse)
def get_shopping_list_detail(
    shopping_list_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.get_list_detail(shopping_list_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return result

# 4. 買い物リストのアイテム一覧取得
@router.get("/{shopping_list_id}/items", response_model=List[ShoppingListItemResponse])
def get_shopping_list_items(
    shopping_list_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.get_items(shopping_list_id, user_id=current_user.id)

# 5. 買い物リストアイテムの更新
@router.put("/item/{shopping_list_item_id}", response_model=ShoppingListItemResponse)
def update_shopping_list_item(
    shopping_list_item_id: int,
    req: UpdateShoppingListItemRequest,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.update_item(shopping_list_item_id, req, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
