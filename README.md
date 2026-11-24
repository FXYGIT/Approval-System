# 简易审批流系统

固定两级串行审批，前后端分离。已实现完整业务闭环：注册登录、申请草稿管理、提交、一级/二级通过与驳回、待办列表、审批历史。技术栈 Vue 3 + TypeScript + FastAPI + MySQL。

## 快速启动

```powershell
Copy-Item .env.example .env   # 配置两个随机数据库密码与至少 32 字节的 JWT_SECRET_KEY
docker compose up --build -d --wait
```

- 前端：http://localhost:5173
- Swagger：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

数据库表由一次性 migrate 服务经 Alembic 创建，`migrate Exited (0)` 为正常状态。

## 开发模式（热更新）

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d --wait
```

后端挂载源码经 Uvicorn 重载，前端挂载源码经 Vite 重载。修改依赖后需重新构建镜像。

## 配置

`.env.example` 提供数据库名/用户/密码、JWT 密钥与有效期、宿主机端口。密钥缺失或占位会阻止启动；数据库不暴露宿主机端口，容器经 `mysql:3306` 连接。`docker compose down` 保留数据卷，`down -v` 删除数据（先确认）。

## 测试与静态检查

```powershell
# 后端（先启动 Compose）
docker compose run --rm --no-deps -e UV_PROJECT_ENVIRONMENT=/tmp/test-venv -v ./backend/tests:/app/tests:ro backend uv run --frozen pytest -q -o cache_dir=/tmp/pytest-cache

# 前端
cd frontend && npm ci && npm run test && npm run build
```

后端 103 项、前端 28 项测试通过，详见[开发记录](docs/07-Development-Log.md)。

## 技术栈

Vue 3 + TypeScript + Vite + Pinia + Vue Router + Element Plus + Axios；Python 3.12 + FastAPI + SQLAlchemy 2.x（同步 Session）+ PyMySQL；MySQL 8.4.7 + Alembic；JWT(HS256) + Argon2id；Docker Compose。

JSON 字段 camelCase，错误统一为 `error.code/message`。完整契约见 [API 设计](docs/04-API-Design.md)。

## 目录

- `backend/src/app/`：`api` → `services` → `repositories` → `models`/`schemas` 分层；`migrations/` 为 Alembic 迁移。
- `frontend/src/`：`api`、`components`、`views`、`stores`、`router`、`types`。
- `docs/`：权威文档。

## 文档

- [需求与范围](docs/01-Project-Spec.md)
- [系统架构](docs/02-System-Architecture.md)
- [数据库设计](docs/03-Database-Design.md)
- [API 设计](docs/04-API-Design.md)
- [开发规范](docs/05-Development-Standards.md)
- [部署指南](docs/06-Deployment-Guide.md)
- [开发记录](docs/07-Development-Log.md)
