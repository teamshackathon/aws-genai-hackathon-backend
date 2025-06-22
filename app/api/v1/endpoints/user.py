import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import user as crud
from app.schemas import user as schemas
from app.schemas.recipe import UserRecipe, UserRecipeUpdate
from app.schemas.shopping import UserShopping, UserShoppingUpdate
from app.services.recipe_service import RecipeService
from app.services.shopping_service import ShoppingService

router = APIRouter()

def get_recipe_service(db: Session = Depends(deps.get_db)) -> RecipeService:
    """
    レシピサービスの依存関係を取得します。
    """
    try:
        return RecipeService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"レシピサービスの初期化に失敗しました: {str(e)}"
        )
    
def get_shopping_service(db: Session = Depends(deps.get_db)) -> ShoppingService:
    try:
        return ShoppingService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ショッピングサービスの初期化に失敗しました: {str(e)}"
        )


# ロガーの設定
logger = logging.getLogger(__name__)

# 自分のユーザー情報を取得するエンドポイント
@router.get("/me", response_model=schemas.UserMe)
def read_users_me(current_user = Depends(deps.get_current_user)) -> Any:
    """
    現在ログインしているユーザー情報を取得
    """
    # 返却するカラムを制限
    current_user = schemas.User.from_orm(current_user)
    logger.info(f"現在のユーザー情報: {current_user.id}")
    return current_user

@router.put("/me", response_model=schemas.UserMe)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    現在ログインしているユーザー情報を更新
    """
    updated_user = crud.update(db=db, db_obj=current_user, obj_in=user_update)
    return schemas.UserMe.from_orm(updated_user)

@router.get("/me/recipes", response_model=list[UserRecipe])
def get_user_recipes(
    ids: str = Query(None, description="レシピIDのカンマ区切りリスト"),
    current_user = Depends(deps.get_current_user),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> list[UserRecipe]:
    """
    ユーザーのレシピ情報をIdsで取得
    - ids: レシピIDのカンマ区切りリスト。指定がない場合は、ユーザーの全レシピを取得します。
    """

    if ids:
        # idsが指定されている場合、カンマ区切りの文字列をリストに変換
        try:
            recipe_ids = [int(id.strip()) for id in ids.split(",") if id.strip().isdigit()]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid recipe IDs format. Please provide a comma-separated list of integers."
            )
        
        # 指定されたIDのレシピのみ取得
        try:
            user_recipes = recipe_service.get_user_recipes_by_ids(user_id=current_user.id, recipe_ids=recipe_ids)
            return [UserRecipe.from_orm(recipe) for recipe in user_recipes]
        except Exception as e:
            logger.error(f"ユーザーレシピ取得エラー: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="ユーザーレシピの取得に失敗しました。"
            )
    # idsが指定されていない場合、ユーザーの全レシピを取得
    try:
        user_recipes = recipe_service.get_user_recipes(user_id=current_user.id)
        return [UserRecipe.from_orm(recipe) for recipe in user_recipes]
    except Exception as e:
        logger.error(f"ユーザーレシピ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="ユーザーレシピの取得に失敗しました。"
        )

@router.get("/me/recipes/{recipe_id}", response_model=UserRecipe)
def get_user_recipe(
    recipe_id: int,
    current_user = Depends(deps.get_current_user),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> UserRecipe:
    """
    ユーザーの特定のレシピ情報を取得
    """
    try:
        user_recipe = recipe_service.get_user_recipe_by_id(user_id=current_user.id, recipe_id=recipe_id)
        if not user_recipe:
            raise ValueError(f"レシピID {recipe_id} のユーザーレシピが見つかりません。")
        
        return UserRecipe.from_orm(user_recipe)
    except ValueError as e:
        logger.error(f"レシピ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.put("/me/recipes/{recipe_id}", response_model=bool)
def update_user_recipe(
    recipe_id: int,
    user_recipe_update: UserRecipeUpdate,
    current_user = Depends(deps.get_current_user),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> bool:
    """
    ユーザーのレシピ情報を更新
    """
    try:
        # ユーザーのレシピ情報を取得

        # 更新処理
        updated_user_recipe = recipe_service.update_user_recipe(
            user_id=current_user.id,
            recipe_id=recipe_id,
            is_favorite=user_recipe_update.is_favorite,
            note=user_recipe_update.note,
            rating=user_recipe_update.rating
        )
        
        if not updated_user_recipe:
            raise ValueError(f"レシピID {recipe_id} のユーザーレシピが見つかりません。")
        

        return True
    except ValueError as e:
        logger.error(f"レシピ更新エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.delete("/me/recipes/{recipe_id}", response_model=bool)
def delete_user_recipe(
    recipe_id: int,
    current_user = Depends(deps.get_current_user),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> bool:
    """
    ユーザーのレシピ情報を削除
    """
    try:
        # ユーザーのレシピ情報を削除
        deleted = recipe_service.delete_user_recipe(
            user_id=current_user.id,
            recipe_id=recipe_id
        )
        if not deleted:
            raise ValueError(f"レシピID {recipe_id} のユーザーレシピが見つかりません。")
        return True
    except ValueError as e:
        logger.error(f"レシピ削除エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.get("/me/shoppings", response_model=list[UserShopping])
def get_user_shoppings(
    ids: str = Query(None, description="ショッピングIDのカンマ区切りリスト"),
    current_user = Depends(deps.get_current_user),
    shopping_service: ShoppingService = Depends(get_shopping_service),
) -> list[UserShopping]:
    """
    ユーザーのショッピング情報を取得
    - ids: ショッピングIDのカンマ区切りリスト。指定がない場合は、ユーザーの全ショッピングを取得します。
    """
    if ids:
        # idsが指定されている場合、カンマ区切りの文字列をリストに変換
        try:
            shopping_ids = [int(id.strip()) for id in ids.split(",") if id.strip().isdigit()]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid shopping IDs format. Please provide a comma-separated list of integers."
            )
        
        # 指定されたIDのショッピングのみ取得
        try:
            user_shoppings = shopping_service.get_user_shoppings_by_ids(user_id=current_user.id, shopping_ids=shopping_ids)
            return [UserShopping.from_orm(shopping) for shopping in user_shoppings]
        except Exception as e:
            logger.error(f"ユーザーショッピング取得エラー: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="ユーザーショッピングの取得に失敗しました。"
            )
    
    # idsが指定されていない場合、ユーザーの全ショッピングを取得
    try:
        user_shoppings = shopping_service.get_user_shoppings(user_id=current_user.id)
        return [UserShopping.from_orm(shopping) for shopping in user_shoppings]
    except Exception as e:
        logger.error(f"ユーザーショッピング取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="ユーザーショッピングの取得に失敗しました。"
        )

@router.get("/me/shoppings/{shopping_id}", response_model=UserShopping)
def get_user_shopping(
    shopping_id: int,
    current_user = Depends(deps.get_current_user),
    shopping_service: ShoppingService = Depends(get_shopping_service),
) -> UserShopping:
    """
    ユーザーの特定のショッピング情報を取得
    """
    try:
        user_shopping = shopping_service.get_user_shopping_by_id(
            user_id=current_user.id,
            shopping_id=shopping_id
        )
        
        if not user_shopping:
            raise ValueError(f"ショッピングID {shopping_id} のユーザーショッピングが見つかりません。")
        
        return UserShopping.from_orm(user_shopping)
    except ValueError as e:
        logger.error(f"ショッピング取得エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.put("/me/shoppings/{shopping_id}", response_model=bool)
def update_user_shopping(
    shopping_id: int,
    user_shopping_update: UserShoppingUpdate,
    current_user = Depends(deps.get_current_user),
    shopping_service: ShoppingService = Depends(get_shopping_service),
) -> bool:
    """
    ユーザーのショッピング情報を更新
    """
    try:
        # ユーザーのショッピング情報を更新
        updated_user_shopping = shopping_service.update_user_shopping(
            user_id=current_user.id,
            shopping_id=shopping_id,
            is_favorite=user_shopping_update.is_favorite,
        )
        
        if not updated_user_shopping:
            raise ValueError(f"ショッピングID {shopping_id} のユーザーショッピングが見つかりません。")
        
        return True
    except ValueError as e:
        logger.error(f"ショッピング更新エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    
