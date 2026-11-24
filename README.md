# 简易审批流系统

固定两级串行审批项目。目前已完成第一阶段工程骨架；注册登录、草稿及审批业务尚未实现。

## 快速启动

需要 Docker Engine / Docker Desktop（Linux containers）和 Docker Compose v2。

```powershell
Copy-Item .env.example .env
# 编辑 .env，设置两个不同的随机数据库密码；不要提交 .env。
docker compose up --build -d --wait
```

- 前端：http://localhost:5173
- Swagger：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health
- 经前端代理的健康检查：http://localhost:5173/api/health

MySQL 健康后，一次性 migrate 自动执行 `alembic upgrade head`；成功后启动后端，再启动前端。`migrate Exited (0)` 是正常状态。三张业务表由 Alembic 创建，不使用 create_all。

## 开发模式

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d --wait
```

地址与验收模式相同。后端挂载 `backend/src` 和 migrations，Uvicorn 自动重载；前端挂载源码，使用 Vite。修改依赖后重新构建镜像。切回验收模式执行快速启动中的命令。

## 配置和数据

`.env.example` 提供数据库名、用户、密码和宿主机端口。数据库不发布宿主机端口，容器通过 `mysql:3306` 连接。应用使用 URL.create 构造连接串，可处理密码特殊字符；dotenv 中含 `$` 的值应使用单引号包裹。后端独立运行也支持 `DATABASE_URL`，但 Compose 默认使用分项变量。

```powershell
docker compose ps -a
docker compose logs migrate
docker compose exec backend alembic current
docker compose exec backend alembic check
docker compose down
```

`down` 保留 `mysql_data` 命名卷；`down -v` 会删除数据，仅在确认可丢弃时使用。已有 volume 的密码不会随 `.env` 修改自动更新。启动问题先查看对应服务日志。

## 技术与目录

- Vue 3 + TypeScript + Vite，验收镜像使用非 root Nginx。
- Python 3.12 + FastAPI + uv，SQLAlchemy 2.x 同步 Session + PyMySQL。
- MySQL 8.4.7、Alembic；依赖版本固定于 uv.lock、package-lock.json。
- `backend/src/app/models/`：User、Request、ApprovalHistory。
- `backend/src/app/db/`：统一 Base、UTC 时间、Session 生命周期。
- `backend/src/app/main.py`：仅 `/api/health`（实际查询数据库，异常返回 503）。
- `backend/migrations/`：独立、可回退的初始迁移。
- `backend/tests/`：真实 MySQL 约束与健康接口测试。
- `frontend/src/`：最小 Vue 入口和统一健康检查请求模块。

本阶段不添加 JWT、Router、Pinia、UI 库等未使用依赖。数据库采用区分大小写的 utf8mb4_0900_as_cs，用户名唯一性也区分大小写；时间按 UTC 保存。

## 验证

先启动 Compose。测试使用随机 ID，数据库写入在测试事务结束时回滚。只在开发/测试数据库运行。

```powershell
docker compose run --rm --no-deps -e UV_PROJECT_ENVIRONMENT=/tmp/test-venv -v ./backend/tests:/app/tests:ro backend uv run --frozen pytest -q -o cache_dir=/tmp/pytest-cache
cd backend
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
```

前端类型检查和生产构建在 `docker compose build frontend` 中执行。迁移回退会删表，必须使用专用临时库验证，不能在有业务数据的库随意执行。

实际验证结果见 [开发记录](docs/07-Development-Log.md)。本阶段通过不代表审批业务验收通过。

## 项目文档

- [需求与范围](docs/01-Project-Spec.md)
- [系统架构](docs/02-System-Architecture.md)
- [数据库设计](docs/03-Database-Design.md)
- [API 设计](docs/04-API-Design.md)
- [开发规范](docs/05-Development-Standards.md)
- [部署指南](docs/06-Deployment-Guide.md)
- [开发记录](docs/07-Development-Log.md)
