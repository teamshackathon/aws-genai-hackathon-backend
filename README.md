# aws-genai-hackathon-backend


```
app/
├── api/                     # API関連コード
│   ├── deps.py              # 依存関係（DBセッションなど）
│   └── v1/                  # APIバージョン1
│       ├── endpoints/       # 各エンドポイント
│       │   └── recipes.py   # レシピ関連エンドポイント
│       └── api.py           # APIルーターの設定
├── core/                    # コア設定
│   ├── config.py            # 環境設定（dev/prod）
│   └── security.py          # 認証関連
├── crud/                    # CRUD操作
│   └── recipe.py            # レシピのCRUD操作
├── db/                      # データベース関連
│   ├── base.py              # モデルのベースクラス
│   ├── base_class.py        # SQLAlchemyのベースクラス
│   ├── init_db.py           # DB初期化スクリプト
│   └── session.py           # DBセッション作成
├── models/                  # SQLAlchemyモデル
│   ├── recipe.py            # レシピモデル
│   └── ...
├── schemas/                 # Pydanticスキーマ
│   ├── recipe.py            # レシピスキーマ
│   └── ...
├── migrations/              # Alembicマイグレーション
│   ├── versions/            # マイグレーションバージョン
│   ├── env.py               # マイグレーション環境
│   └── script.py.mako       # テンプレート
├── tests/                   # テスト
│   ├── conftest.py          # テスト設定
│   └── api/                 # APIテスト
│       └── v1/              
│           └── test_recipes.py
├── main.py                  # アプリケーションのエントリーポイント
├── alembic.ini              # Alembic設定
└── .env.example   
```