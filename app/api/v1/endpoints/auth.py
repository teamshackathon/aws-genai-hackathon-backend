import secrets
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import generate_state_token
from app.crud import user as crud
from app.schemas import user as schemas

router = APIRouter()

@router.post("/login/password", response_model=schemas.Token)
def login_password(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    メールアドレスとパスワードによる認証
    
    - **username**: メールアドレス
    - **password**: パスワード
    """
    user = crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="メールアドレスまたはパスワードが正しくありません")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="ユーザーは無効です")
    
    # ログイン時間を更新
    crud.update_login_time(db=db, user=user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 秒単位
    }

@router.post("/register", response_model=schemas.User)
def register_new_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    新しいユーザーを登録
    """
    user = crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="このメールアドレスはすでに登録されています。",
        )
    user = crud.create(db, obj_in=user_in)
    return user

@router.get("/login/github")
async def login_github(request: Request):
    """
    GitHub OAuth認証のリダイレクトURLを生成
    """
    # セッションIDを取得またはCookieから生成
    session_id = request.cookies.get("session_id")
    print(f"Session ID: {session_id}")
    if not session_id:
        session_id = secrets.token_urlsafe(16)
    
    # stateトークンを生成
    state = generate_state_token(session_id)
    
    # GitHub認証URL生成
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "user:email",
        "state": state,
    }
    github_auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    # セッションIDをCookieに設定してリダイレクト
    response = RedirectResponse(url=github_auth_url)
    response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="none")
    return response

@router.get("/callback/github")
async def github_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(deps.get_db),
):
    """
    GitHub OAuth認証のコールバック処理
    
    GitHubから返されたコードを使用してアクセストークンを取得し、
    ユーザー情報を取得してデータベースに保存します。
    認証成功後はJWTトークンを生成して返します。
    """
    # 認証コードの検証
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="認証コードが見つかりません"
        )
    
    # セッションIDを取得
    # if settings.ENVIRONMENT == "production":
    #     session_id = request.cookies.get("session_id")
    #     print(f"Session ID from callback: {session_id}")
    #     if not session_id:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="セッションIDが見つかりません"
    #         )
        
    #     # stateトークンを検証
    #     if not verify_state_token(session_id, state):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="不正なリクエスト - stateトークンが無効です"
    #         )
    
    # GitHubからアクセストークンを取得
    token_url = "https://github.com/login/oauth/access_token"
    
    token_payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    
    headers = {
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # アクセストークン取得
        token_response = await client.post(token_url, json=token_payload, headers=headers)
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHubからのトークン取得に失敗しました"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHubからのアクセストークン取得に失敗しました"
            )
        
        # GitHubからユーザー情報を取得
        user_api_url = "https://api.github.com/user"
        user_email_url = "https://api.github.com/user/emails"
        
        auth_headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json"
        }
        
        # ユーザープロファイルを取得
        user_response = await client.get(user_api_url, headers=auth_headers)
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHubからのユーザー情報取得に失敗しました"
            )
        
        github_user = user_response.json()
        
        # ユーザーのメールアドレスを取得
        email_response = await client.get(user_email_url, headers=auth_headers)
        
        if email_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHubからのメールアドレス取得に失敗しました"
            )
        
        emails = email_response.json()
        primary_email = next((email.get("email") for email in emails if email.get("primary")), None)
        
        if not primary_email:
            primary_email = emails[0].get("email") if emails else None
        
        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHubからのメールアドレス取得に失敗しました"
            )
        
        # データベースにユーザーがすでに存在するか確認
        user = crud.get_by_oauth_id(db, provider="github", oauth_id=str(github_user.get("id")))
        
        if not user:
            # メールアドレスで検索
            user = crud.get_by_email(db, email=primary_email)
            
            if user:
                # 既存ユーザーにGitHub情報を追加
                if not user.oauth_provider:
                    user_update = {
                        "oauth_provider": "github",
                        "oauth_id": str(github_user.get("id")),
                        "github_username": github_user.get("login"),
                        "github_avatar_url": github_user.get("avatar_url"),
                    }
                    user = crud.update(db, db_obj=user, obj_in=user_update)
            else:
                # 新規ユーザーの作成
                user_oauth_data = schemas.UserOAuthCreate(
                    email=primary_email,
                    name=github_user.get("name") or github_user.get("login"),
                    oauth_provider="github",
                    oauth_id=str(github_user.get("id")),
                    github_username=github_user.get("login"),
                    github_avatar_url=github_user.get("avatar_url"),
                )
                user = crud.create_oauth_user(db, obj_in=user_oauth_data)
        
        # ログイン時間を更新
        crud.update_login_time(db=db, user=user)
        
        # JWTトークンの生成
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # フロントエンドのURLにトークン情報をクエリパラメータとして追加してリダイレクト
        frontend_url = settings.FRONTEND_REDIRECT_URL
        redirect_params = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": str(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        }
        print(f"{frontend_url}/auth/callback?{urlencode(redirect_params)}")
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?{urlencode(redirect_params)}"
        )