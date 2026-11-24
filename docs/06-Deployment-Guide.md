# 06 — 部署与运行指南（Deployment Guide）

| 属性 | 内容 |
|---|---|
| 文档编号 | DEPLOY-006 |
| 版本 | V0.3 |
| 容器策略 | 开发和验收均使用 Docker Compose |

## 1. 目标

开发和验收环境均通过 Docker Compose 管理前端、后端和 MySQL。开发模式支持代码热更新；验收模式使用构建后的镜像。

## 2. 服务规划

| 服务 | 职责 |
|---|---|
| frontend | Vue 开发服务器或 Nginx 静态站点 |
| backend | FastAPI |
| mysql | MySQL 数据库 |
| migrate | 一次性 Alembic 迁移任务 |

migrate 执行成功后退出，不是长期运行服务。

## 3. 环境变量

根目录提供 `.env.example`，实际运行时复制为 `.env`。

建议变量：

```dotenv
MYSQL_DATABASE=approval_db
MYSQL_USER=approval_user
MYSQL_PASSWORD=replace_with_db_password
MYSQL_ROOT_PASSWORD=replace_with_root_password

DATABASE_URL=mysql+pymysql://approval_user:replace_with_db_password@mysql:3306/approval_db?charset=utf8mb4

JWT_SECRET_KEY=replace_with_a_secure_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

APP_ENV=development
LOG_LEVEL=INFO
```

说明：
- 上述为变量示例，密码和密钥必须替换。
- `.env` 不提交 Git。
- 容器内部通过服务名 `mysql` 连接数据库，不使用 localhost。
- URL 中的特殊字符需正确编码。
- JWT 算法和过期时间应与安全实现保持一致。

## 4. Compose 服务依赖

```mermaid
flowchart TD
    A[Compose up] --> B[MySQL]
    B --> C{Healthcheck healthy?}
    C -->|No| B
    C -->|Yes| D[Alembic migration]
    D --> E{Migration success?}
    E -->|No| F[Backend not started]
    E -->|Yes| G[FastAPI backend]
    G --> H[Frontend]
```

MySQL 使用 healthcheck。迁移服务等待数据库健康。后端等待迁移服务成功完成。不能只依赖容器启动顺序判断数据库已可用。

## 5. 开发模式

开发 Compose 文件建议使用：
- backend：挂载 `backend/src/app` 和迁移目录，运行 Uvicorn `--reload`。
- frontend：使用 Node 镜像，运行 Vite `--host 0.0.0.0`，挂载源码。
- mysql：使用持久化 volume。

启动命令：

```bash
cp .env.example .env

docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up --build
```

建议开发地址：
- Frontend：`http://localhost:5173`
- Backend：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

Vite 通过代理将 `/api` 请求转发至 `http://backend:8000`。

## 6. 验收模式

验收模式构建前端静态资源并通过 Nginx 提供服务，后端运行 FastAPI。

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f backend
docker compose logs migrate
```

建议默认入口：
- Frontend：`http://localhost:5173`（取决于 Compose 端口映射）
- Backend：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

实际端口以最终 Compose 配置为准。

## 7. 数据库持久化与清理

MySQL 数据目录必须挂载命名 volume。

停止服务：

```bash
docker compose down
```

此命令保留命名 volume。

彻底删除容器及数据库数据：

```bash
docker compose down -v
```

执行前确认数据可删除。验收时应验证容器重建后数据库数据仍然存在。

## 8. Alembic 迁移

迁移由一次性 migrate 服务运行：

```bash
uv run alembic upgrade head
```

本地排查可使用：

```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```

迁移文件必须提交 Git。自动生成迁移后要人工检查外键、索引、CHECK 约束、默认值及字段类型。

## 9. 镜像与安全约定

- Python 基础镜像使用 Python 3.12。
- Node 仅用于前端构建或开发。
- 最终前端镜像可使用 Nginx。
- 依赖使用锁文件安装。
- 正式验收镜像应固定基础镜像版本，避免长期使用 `latest`。
- 容器尽可能以非 root 用户运行。
- 不在镜像中烘焙真实密钥。
- 生产环境不应无条件暴露 MySQL 端口。
- 日志不得包含密码、JWT 完整值或密钥。

## 10. 部署验收清单

- [ ] `.env` 配置正确且未提交。
- [ ] MySQL healthcheck 成功。
- [ ] Alembic migration 成功。
- [ ] migration 失败时后端不启动。
- [ ] FastAPI 正常启动。
- [ ] 前端能够访问后端 API。
- [ ] Swagger 可访问。
- [ ] MySQL volume 能持久化数据。
- [ ] 开发模式前后端代码热更新可用。
- [ ] 验收模式使用构建镜像运行。
- [ ] 新环境可按本指南复现启动。


## 第一阶段实际运行说明（2026-11-24）

以根目录 README 和 Compose 为实际命令依据。当前无需 JWT 环境变量；认证尚未实现。Compose 使用 MYSQL_* 分项配置，通过 URL.create 构造数据库 URL，不要求手写 DATABASE_URL。开发与验收均映射宿主机 5173 → 前端容器 8080；后端 8000。MySQL 8.4.7 不暴露宿主机端口。运行镜像只安装运行依赖，测试通过 README 中临时测试虚拟环境执行。
