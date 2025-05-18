# 🧠 GitHub Copilot Instructions for FastAPI Project

## 🎯 Project Goal

This FastAPI-based web application is designed to support a cooking assistant called "BAE-RECIPE." The app extracts structured recipe data (ingredients, steps, tips) from video content using Bedrock, and helps users manage and browse recipes with beautiful presentation.

## ✅ Requirements Summary

- Use FastAPI with SQLAlchemy (ORM) and Alembic for database migrations.
- Expose RESTful endpoints with automatic Swagger UI docs.
- Use PostgreSQL for production and SQLite for test environments.
- Organize source code with clear separation of concerns (models, schemas, CRUD, APIs, etc.).
- Write clean, isolated unit tests using `pytest` and `httpx`.
- Structure endpoints under `/api/v1`.
- Use Pydantic for data validation and serialization.
- Use dependency injection for database sessions.
- Enable Alembic migration auto-generation from SQLAlchemy models.

## 🗂️ Project Structure

```plaintext
app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── endpoints/
│       │   └── *.py
│       └── api.py
├── core/
│   └── config.py
├── crud/
│   └── *.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── migrations/
├── models/
│   └── *.py
├── schemas/
│   └── *.py
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   └── test_*
├── main.py
└── alembic.ini
