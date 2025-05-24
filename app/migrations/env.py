from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base  # importすべき全モデルがインポートされる

# Alembic設定
config = context.config

# メタデータにモデルを設定
target_metadata = Base.metadata

# 環境変数からDB URIを設定
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

def run_migrations_online():
    # 実際のマイグレーション実行コード
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()