# 06 — 部署与运行指南（Deployment Guide）

| 属性 | 内容 |
|---|---|
| 文档编号 | DEPLOY-006 |
| 版本 | V1.0 |
| 容器策略 | 开发与验收均使用 Docker Compose |

## 1. 服务规划

| 服务 | 职责 |
|---|---|
| mysql | MySQL 数据库 |
| migrate | 一次性 Alembic 迁移，成功后退出 |
| backend | FastAPI |
| frontend | Vue 开发服务器（开发）或 Nginx 静态站点（验收） |

## 2. 环境变量

根目录 `.env.example` 复制为 `.env` 后填写：

```dotenv
MYSQL_DATABASE=approval_db
MYSQL_USER=approval_user
MYSQL_PASSWORD=<随机数据库密码>
MYSQL_ROOT_PASSWORD=<随机 root 密码>

JWT_SECRET_KEY=<至少 32 字节随机密钥>
JWT_EXPIRE_MINUTES=60

BACKEND_PORT=8000
FRONTEND_PORT=5173
```

`.env` 不提交 Git。数据库密码与密钥必须替换，密钥缺失或占位会阻止启动。容器经服务名 `mysql:3306` 连接数据库，不发布宿主机端口。

## 3. 启动

验收模式：

```powershell
docker compose up --build -d --wait
```

开发模式（热更新）：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d --wait
```

入口：前端 http://localhost:5173、后端/Swagger http://localhost:8000/docs、健康检查 http://localhost:8000/api/health。

## 4. 依赖顺序

MySQL healthcheck 通过 → migrate 执行 `alembic upgrade head` → 成功（Exited 0）→ backend 启动 → frontend 启动。迁移失败时 backend 不启动。不能只依赖容器启动顺序判断数据库可用。

## 5. 数据持久化与清理

MySQL 数据挂载命名卷 `mysql_data`。`docker compose down` 保留数据；`down -v` 删除数据，仅确认可丢弃时使用。已有卷的密码不随 `.env` 修改自动更新。

## 6. 迁移与排查

迁移由 migrate 服务自动执行；排查用：

```powershell
docker compose ps -a
docker compose logs migrate
docker compose exec backend alembic current
docker compose exec backend alembic check
```

迁移文件必须提交 Git；autogenerate 后人工检查外键、索引、CHECK 约束、默认值与字段类型。回退会删表，须用专用临时库验证。

## 7. 镜像与安全

依赖以锁文件安装；正式镜像固定基础镜像版本，容器尽量以非 root 运行；不在镜像烘焙密钥；不无条件暴露 MySQL 端口；日志不含密码、JWT 完整值或密钥。
