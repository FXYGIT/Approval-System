# Approval API

源码采用 src 布局，入口为 app.main:app。完整 Compose 启动、环境变量与测试说明见根目录 README.md。

本地工具：uv sync --frozen、uv run ruff check .。本地运行 API 或 Alembic 前，需设置 DATABASE_URL，或 MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE。
