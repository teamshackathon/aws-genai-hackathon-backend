from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core.aws.polly_client import PollyClient
from app.models.user import Users
from app.schemas.recipe import ExternalService, Ingredient, Process, Recipe, RecipeList, RecipeStatus, VoiceReaderInput
from app.services.recipe_service import RecipeService

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

def get_polly_client():
    """Amazon Polly clientを取得"""
    try:
        polly_client = PollyClient()
        return polly_client.get_client()
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Failed to initialize Amazon Polly client. Please check AWS credentials."
        )

# ページネーション付きのレシピ一覧を取得
@router.get("", response_model=RecipeList)
def get_recipes(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりのレシピ数"),
    keyword: Optional[str] = Query(None, description="検索キーワード"),
    favorites_only: bool = Query(False, description="お気に入りのみを取得するかどうか"),
    sorted_by: Optional[str] = Query(None, description="ソート条件"),
    order_by: Optional[str] = Query(None, description="ソート順（ascまたはdesc）"),
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> RecipeList:
    """
    ページネーション付きのレシピ一覧を取得します。
    """
    return recipe_service.get_recipes(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        keyword=keyword,
        favorites_only=favorites_only,
        sorted_by=sorted_by,
        order_by=order_by
    )

@router.get("/external-services", response_model=list[ExternalService])
def get_external_services(
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> list[ExternalService]:
    """
    外部サービスの一覧を取得します。
    """
    return recipe_service.get_external_services()

@router.get("/statuses", response_model=list[RecipeStatus])
def get_recipe_statuses(
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> list[RecipeStatus]:
    """
    レシピステータスの一覧を取得します。
    """
    return recipe_service.get_recipe_statuses()

@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe_by_id(
    recipe_id: int, 
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> Recipe:
    """
    指定されたIDの単一レシピを取得します。
    """
    recipe = recipe_service.get_recipe_by_id(recipe_id, current_user.id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get("/{recipe_id}/ingredients", response_model=List[Ingredient])
def get_ingredients_by_recipe_id(
    recipe_id: int,
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> List[Ingredient]:
    """
    指定されたレシピIDの材料を取得します。
    """
    ingredients = recipe_service.get_ingredient_by_recipe_id(recipe_id)
    if not ingredients:
        raise HTTPException(status_code=404, detail="Ingredients not found for this recipe")
    return ingredients

@router.get("/{recipe_id}/processes", response_model=List[Process])
def get_processes_by_recipe_id(
    recipe_id: int,
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> List[Process]:
    """
    指定されたレシピIDの調理手順を取得します。
    """
    processes = recipe_service.get_processes_by_recipe_id(recipe_id)
    if not processes:
        raise HTTPException(status_code=404, detail="Processes not found for this recipe")
    return processes

@router.post("/process/voice_reader")
def read_process_voice(
    input: VoiceReaderInput,
    polly_client=Depends(get_polly_client),
    current_user: Users = Depends(deps.get_current_user)
):
    """
    指定されたテキストを音声で読み上げます。
    """
    if not input.text:
        raise HTTPException(
            status_code=400, detail="音声化するテキストが指定されていません。"
        )
    
    try:
        # Amazon Pollyを使用して音声を生成
        response = polly_client.synthesize_speech(
            Text=input.text,
            OutputFormat='mp3',
            VoiceId="Takumi",  # 日本語の音声を使用
            LanguageCode='ja-JP'
        )

        audio_stream = response.get("AudioStream")
        if not audio_stream:
            raise HTTPException(
                status_code=500, detail="音声の生成に失敗しました。"
            )
        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=voice.mp3"}
        )
    except Exception as e:
        print(f"音声生成に失敗しました: {e}")
        raise HTTPException(
            status_code=500, detail=f"音声生成に失敗しました。{str(e)}"
        )