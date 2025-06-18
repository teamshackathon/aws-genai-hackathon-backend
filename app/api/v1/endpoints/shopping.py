from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import Users
from app.schemas.shopping import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate, ShoppingList, ShoppingListCreate, ShoppingListDetail, ShoppingListUpdate
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

# ショッピングリスト一覧取得
@router.get("", response_model=List[ShoppingList])
def get_shopping_lists(
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.get_lists(user_id=current_user.id)

# ショッピングリスト詳細取得（アイテム含む）
@router.get("/{list_id}", response_model=ShoppingListDetail)
def get_shopping_list_detail(
    list_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.get_list_detail(list_id=list_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return result

# ショッピングリスト作成
@router.post("", response_model=ShoppingList)
def create_shopping_list(
    shopping_list: ShoppingListCreate,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.create_list(shopping_list, user_id=current_user.id)

# ショッピングリスト更新
@router.put("/{list_id}", response_model=ShoppingList)
def update_shopping_list(
    list_id: int,
    shopping_list: ShoppingListUpdate,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.update_list(list_id, shopping_list, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return result

# ショッピングリスト削除
@router.delete("/{list_id}")
def delete_shopping_list(
    list_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    success = shopping_service.delete_list(list_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return {"result": "deleted"}

# アイテム追加
@router.post("/{list_id}/items", response_model=ShoppingItem)
def add_item(
    list_id: int,
    item: ShoppingItemCreate,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    return shopping_service.add_item(list_id, item, user_id=current_user.id)

# アイテム更新
@router.put("/{list_id}/items/{item_id}", response_model=ShoppingItem)
def update_item(
    list_id: int,
    item_id: int,
    item: ShoppingItemUpdate,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    result = shopping_service.update_item(list_id, item_id, item, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result

# アイテム削除
@router.delete("/{list_id}/items/{item_id}")
def delete_item(
    list_id: int,
    item_id: int,
    shopping_service: ShoppingService = Depends(get_shopping_service),
    current_user: Users = Depends(deps.get_current_user)
):
    success = shopping_service.delete_item(list_id, item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"result": "deleted"}
