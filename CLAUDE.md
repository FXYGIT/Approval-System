# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目状态

当前已完成**第五阶段前端审批工作台与审批历史**：注册、登录、JWT、当前用户、用户候选列表、草稿 CRUD，申请提交、一级/二级通过与驳回、审批历史记录与查询、待审批列表，以及前端完整闭环——基础架构（Vue Router、Pinia、Axios 封装、JWT 持久化、统一异常处理）、申请管理页面（我的申请列表、创建、草稿编辑/删除、详情）、待我审批列表、审批操作（通过/驳回，动态权限）、审批历史时间线与草稿提交。用户可完全通过浏览器完成「提交→一级审批→二级审批」或任一级驳回的完整流程。`docs/` 下的文档是权威来源，`README.md` 只作入口和运行说明。任何实施工作前应先读对应文档，而非凭默认假设编码。

技术选型分三档，不能混用：
- **已确定**：Vue 3 + TypeScript、Python 3.12 + FastAPI、uv、SQLAlchemy 2.x 同步 Session、MySQL、Alembic、Docker Compose（开发/验收均用）、Vite、Vue Router、Pinia、Axios、Element Plus、PyMySQL、Argon2id、HS256、MySQL 8.4.7。
- **待确认**：无（原候选——JWT 有效期 60 分钟、Token 前端存 localStorage、错误格式 error.code/message、密码 8–128 字符均已确定，见 docs/04）。
- 前端新增依赖版本由 package.json / package-lock.json 固定，遵循 README 的 `npm ci`。

## 文档导航（权威来源）

| 文档 | 内容 |
|---|---|
| `docs/01-Project-Spec.md` | 业务需求、范围、角色权限、状态机、验收条件。业务规则的唯一主要维护位置。 |
| `docs/02-System-Architecture.md` | 技术架构、模块边界、事务边界、并发策略、ADR。 |
| `docs/03-Database-Design.md` | ER 图、表结构、索引、ORM 约定、Alembic 命令。 |
| `docs/04-API-Design.md` | 接口清单、请求/响应约定、错误码。 |
| `docs/05-Development-Standards.md` | 代码组织、命名、Git、测试、AI 辅助开发规范。 |
| `docs/06-Deployment-Guide.md` | 环境变量、Docker Compose、启动/验收。 |
| `docs/07-Development-Log.md` | 进度与决策变更记录（需随开发更新）。 |

## 命令

命令以根目录 README 为准。Python 依赖及 uv.lock 已提供；FastAPI 入口为 backend/src/app/main.py。容器运行环境不安装测试依赖，测试命令见 README。

Python 依赖与运行（在 `backend/` 目录下，用 uv）：

```bash
uv sync --frozen          # 按锁文件安装依赖
uv add <pkg>              # 添加运行依赖
uv add --dev <pkg>        # 添加开发依赖
uv lock                   # 更新锁文件
uv run pytest             # 跑测试（用 --cov 加覆盖率）
uv run ruff check .       # lint
uv run uvicorn app.main:app --reload   # 本地起服务（文档目录约定 app/main.py）
```

Alembic 迁移（在 `backend/` 目录下，迁移目录 `backend/migrations/`）：

```bash
uv run alembic revision --autogenerate -m "create initial tables"
uv run alembic upgrade head
uv run alembic current
uv run alembic history
uv run alembic downgrade -1
```

Docker Compose（开发与验收均为正式启动方式，见 `docs/06`）：

```bash
cp .env.example .env      # 先配置密码与 JWT 密钥
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build   # 开发模式（热更新）
docker compose up --build -d     # 验收模式
docker compose down              # 停止（保留 volume）
docker compose down -v           # 删除数据（先确认）
```

## 架构

前后端分离，前端只通过 HTTP API（JWT Bearer）访问后端，不得直连数据库。

后端分层与依赖方向（严格单向）：**API（Router）→ Service → Repository → SQLAlchemy → MySQL**。

- **API 层**（`app/api/`）：HTTP 接收、Pydantic 校验、认证依赖、调用 Service、组织响应。不得堆积业务逻辑。
- **Service 层**（`app/services/`）：业务规则、权限判断、状态流转，并**明确开启/提交事务**。审批关键路径在此实现并发控制。
- **Repository 层**（`app/repositories/`）：查询与持久化，不决定业务、不负责 HTTP 状态码、不擅自提交事务。
- **Model vs Schema**（`app/models/`、`app/schemas/`）：ORM 映射与 API 输入输出分离，不可混用。

每个 HTTP 请求独立 Session，请求结束关闭；FastAPI 依赖只管理 Session 生命周期，事务由 Service 提交/回滚。

## 核心业务不变量（跨文档，最易出错处）

**两级串行审批状态机**——合法的 `(status, current_step)` 组合只有五种：

| Status | CurrentStep |
|---|---|
| Draft | NULL |
| InProgress | First |
| InProgress | Second |
| Approved | NULL |
| Rejected | NULL |

提交：`Draft→InProgress/First`；一级通过：`First→Second`；二级通过：`Second→Approved`；任一节点驳回：`→Rejected`。不允许跳节点、重复审批、审批已结束申请。驳回意见必填（≤500 字符），通过意见可空。本期**不做**驳回后重提、撤回、会签、转交、动态审批人。

**权限**：申请人由 Token 确定（不信任客户端传 `applicant_id`/`operator_id`/`current_step`）。申请人不能指定自己为任一级审批人。一级/二级审批人可为同一人，但须分别完成两步。无关用户访问详情/历史返回 403。

**事务与并发（乐观锁）**：`requests` 表有 `version` 列（初始 1）。提交/通过/驳回必须在**同一事务**内更新 `requests` 并新增 `approval_histories`。审批用**条件 UPDATE**，WHERE 至少含 `id`、读取时 `version`、预期 `status`、预期 `current_step`、当前节点审批人；更新时 `version = version + 1`，仅当 `rowcount == 1` 才写历史，否则回滚并返回 409。权限错误（非当前审批人）返回 403，有权限但状态过期返回 409，两者必须区分。注意 `version_id_col` 只对 ORM 普通对象更新生效，显式批量 UPDATE 不自动套用，审批路径必须显式写版本条件并检查 rowcount。

## 实施易错点

- **时间列**：MySQL 微秒精度用 `sqlalchemy.dialects.mysql.DATETIME(fsp=6)`，不要把 `fsp` 传给通用 `DateTime`。
- **UUID 主键**：`CHAR(36)`，应用层 `str(uuid.uuid4())`。
- **多外键 relationship**：`Request` 对 `users` 有三条外键（applicant/first_approver/second_approver），relationship 必须显式指定 `foreign_keys`，否则歧义。
- **待审批列表**：只能查 `status = InProgress` 且当前步骤对应审批人 == 当前用户（First 匹配 `first_approver_id`，Second 匹配 `second_approver_id`），不能只按审批人字段查。
- **历史排序**：`created_at ASC, id ASC` 稳定排序。删除草稿不产生历史。业务 API 只提供历史新增和查询。
- **索引**：见 `docs/03` 第 6 节，需用 `EXPLAIN` 验证。
- **迁移**：不得用 `Base.metadata.create_all()` 代替 Alembic；autogenerate 后人工检查外键、索引、CHECK 约束、默认值、时间精度。
- **实际源码布局**：保留 backend/src/app，FastAPI 入口 app.main:app；不再保留桩 main()。

## Git 与交付约定

- 提交格式 `<type>: <description>`（feat/fix/refactor/test/docs/chore/style），一个提交对应一个清晰变更，不最后一天一次性提交。
- 不提交 `.env`、密钥、`.venv`、`node_modules`、构建产物；`.gitignore` 需覆盖前后端生成文件。
- 不要自动 commit/push，除非明确要求；提交前展示变更摘要。

当前已采用 Vite、PyMySQL、MySQL 8.4.7、Argon2id、HS256；JWT 默认 60 分钟，错误格式 error.code/message，密码 8–128 字符。具体契约见 docs/04，其他候选项留待对应阶段。
