# 简易审批流系统

固定两级串行审批项目。已完成工程骨架、后端认证与申请草稿管理、提交与两级审批业务，以及前端认证与申请管理页面（注册、登录、退出、我的申请列表、创建、草稿编辑/删除、详情）。审批工作台与审批历史页面尚未实现。

## 快速启动

需要 Docker Engine / Docker Desktop（Linux containers）和 Docker Compose v2。

```powershell
Copy-Item .env.example .env
# 编辑 .env，设置两个不同的随机数据库密码，以及至少 32 字节的随机 JWT_SECRET_KEY；不要提交 .env。
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

`.env.example` 提供数据库名、用户、密码、JWT 密钥/有效期和宿主机端口。已有第一阶段 .env 需要补充 JWT_SECRET_KEY 与 JWT_EXPIRE_MINUTES=60；缺失或占位密钥会阻止 API 启动。数据库不发布宿主机端口，容器通过 `mysql:3306` 连接。应用使用 URL.create 构造连接串，可处理密码特殊字符；dotenv 中含 `$` 的值应使用单引号包裹。后端独立运行也支持 `DATABASE_URL`，但 Compose 默认使用分项变量。

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
- `backend/src/app/main.py`：路由和异常处理装配；`api/deps.py` 提供统一 JWT 认证依赖。
- `backend/migrations/`：独立、可回退的初始迁移。
- `backend/src/app/api/`、`services/`、`repositories/`：认证、用户和草稿的路由、业务及数据访问层。`schemas/` 定义请求/响应契约。
- `backend/tests/`：真实 MySQL 约束、认证、草稿生命周期、审批流转、安全与竞争测试。
- `frontend/src/`：Vue Router 路由、Pinia 状态、Axios 请求封装与统一异常处理、JWT 持久化；登录/注册页、我的申请列表、申请创建、草稿编辑与详情页。

认证使用 PyJWT + Argon2id；前端通过 HTTP API（JWT Bearer）访问后端，不直连数据库。数据库采用区分大小写的 utf8mb4_0900_as_cs，用户名唯一性也区分大小写；时间按 UTC 保存。

## 验证

先启动 Compose。测试使用随机 ID，常规数据库写入在外层事务结束时回滚；两连接竞争测试会提交独立 UUID 探针，并在 finally 中删除。只在开发/测试数据库运行。

```powershell
docker compose run --rm --no-deps -e UV_PROJECT_ENVIRONMENT=/tmp/test-venv -v ./backend/tests:/app/tests:ro backend uv run --frozen pytest -q -o cache_dir=/tmp/pytest-cache
cd backend
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
```

前端测试、类型检查与生产构建：

```powershell
cd frontend
npm ci
npm run test          # vitest 组件/单元测试
npm run build         # vue-tsc --noEmit + vite build
```

`docker compose build frontend` 会在镜像内执行同样的类型检查与生产构建。迁移回退会删表，必须使用专用临时库验证，不能在有业务数据的库随意执行。

实际验证结果见 [开发记录](docs/07-Development-Log.md)。当前后端 103 项测试、前端 15 项测试通过；第三方 Starlette/httpx 有一条弃用提示，不影响结果。后端审批业务与前端认证/申请管理页面已通过，审批工作台与历史页面尚未实现。

## 项目文档

- [需求与范围](docs/01-Project-Spec.md)
- [系统架构](docs/02-System-Architecture.md)
- [数据库设计](docs/03-Database-Design.md)
- [API 设计](docs/04-API-Design.md)
- [开发规范](docs/05-Development-Standards.md)
- [部署指南](docs/06-Deployment-Guide.md)
- [开发记录](docs/07-Development-Log.md)

## 接口使用

在 Swagger 注册两个以上用户，用 `/api/auth/login` 获取 accessToken，点击 Authorize 填入令牌，再调用 `/api/users/me`、`/api/users` 和 `/api/requests`。创建草稿只传 title/content/firstApproverId/secondApproverId；编辑还需 version。申请人用 `/submit` 提交后，一级审批人用 `/approve` 或 `/reject`，二级审批人再操作一次，最终进入 Approved/Rejected；用 `/history` 查看流转，用 `scope=pending` 查看待审批。客户端不能指定申请人、操作人或流程状态。

成功直接返回 DTO，JSON 使用 camelCase；错误统一为 error.code/message。完整请求、响应、权限和错误码见 [API 契约](docs/04-API-Design.md)。用户名区分大小写，密码 8–128 字符且保留首尾空格，JWT 默认有效期 60 分钟，无刷新/注销接口。

安全配置细节见 [系统架构](docs/02-System-Architecture.md)。容器的健康检查无需登录；其余业务接口除注册、登录均需 JWT。
