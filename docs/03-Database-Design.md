# 03 — 数据库设计（Database Design）

| 属性 | 内容 |
|---|---|
| 文档编号 | DB-003 |
| 版本 | V0.3 |
| 数据库 | MySQL |
| ORM | SQLAlchemy 2.x，同步 Session |
| 迁移 | Alembic |

## 1. 数据库约定

- 存储引擎：InnoDB。
- 字符集：utf8mb4。
- 主键：UUID，初期采用 CHAR(36)。
- 时间：统一按 UTC 存储，API 使用 ISO 8601。
- 外键删除策略：RESTRICT。
- 具体 MySQL 小版本在工程配置中固定；MySQL 8.4 LTS 可作为候选版本，需确认运行环境支持。

## 2. ER 图

![ER图](./figures/ER.png)

## 3. users 表

| 字段 | 类型 | 约束 |
|---|---|---|
| id | CHAR(36) | PK |
| username | VARCHAR(50) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| display_name | VARCHAR(100) | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |

规则：用户名唯一；密码只保存安全哈希；本期不提供普通用户删除账户功能。

## 4. requests 表

| 字段 | 类型 | 约束 |
|---|---|---|
| id | CHAR(36) | PK |
| title | VARCHAR(100) | NOT NULL |
| content | VARCHAR(2000) | NOT NULL |
| status | VARCHAR(20) | NOT NULL |
| applicant_id | CHAR(36) | FK users.id, NOT NULL |
| first_approver_id | CHAR(36) | FK users.id, NOT NULL |
| second_approver_id | CHAR(36) | FK users.id, NOT NULL |
| current_step | VARCHAR(20) | NULL |
| version | INT | NOT NULL, DEFAULT 1 |
| created_at | DATETIME(6) | NOT NULL |
| updated_at | DATETIME(6) | NOT NULL |
| submitted_at | DATETIME(6) | NULL |

合法状态：
- Draft + NULL
- InProgress + First
- InProgress + Second
- Approved + NULL
- Rejected + NULL

约束：
- applicant_id 不得等于 first_approver_id。
- applicant_id 不得等于 second_approver_id。
- 审批人必须关联现存用户。
- version >= 1。
- 状态和步骤组合通过 CHECK 约束限制。
- 申请人和审批人规则同时在 Service 层校验。

## 5. approval_histories 表

| 字段 | 类型 | 约束 |
|---|---|---|
| id | CHAR(36) | PK |
| request_id | CHAR(36) | FK requests.id, NOT NULL |
| action | VARCHAR(30) | NOT NULL |
| operator_id | CHAR(36) | FK users.id, NOT NULL |
| step | VARCHAR(20) | NULL |
| comment | VARCHAR(500) | NULL |
| previous_status | VARCHAR(20) | NULL |
| previous_step | VARCHAR(20) | NULL |
| new_status | VARCHAR(20) | NOT NULL |
| new_step | VARCHAR(20) | NULL |
| created_at | DATETIME(6) | NOT NULL |

Action 允许值：
- Submit
- FirstApprove
- FirstReject
- SecondApprove
- SecondReject

创建草稿和删除草稿不生成审批历史。每次成功提交或审批操作必须在同一事务中新增历史记录。普通业务 API 不提供历史更新和删除功能。

## 6. 索引规划

| 表 | 索引 | 用途 |
|---|---|---|
| users | UNIQUE(username) | 登录和唯一性 |
| requests | (applicant_id, created_at, id) | 我发起的列表 |
| requests | (first_approver_id, status, current_step, created_at, id) | 一级待审批 |
| requests | (second_approver_id, status, current_step, created_at, id) | 二级待审批 |
| approval_histories | (request_id, created_at, id) | 历史查询及稳定排序 |

标题关键词初期可使用 LIKE；是否需要全文索引由实际数据规模和查询计划决定。索引最终应通过 EXPLAIN 验证。

## 7. SQLAlchemy 模型实现约定

所有模型继承统一 Declarative Base。字段类型、外键、索引和 CHECK 约束应与本文件保持一致。

建议文件：
- `backend/src/app/db/base.py`
- `backend/src/app/models/user.py`
- `backend/src/app/models/request.py`
- `backend/src/app/models/approval_history.py`

### 7.1 Base

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 7.2 时间字段

MySQL 微秒精度时间类型使用 MySQL 方言类型，例如：

```python
from sqlalchemy.dialects.mysql import DATETIME

created_at = mapped_column(
    DATETIME(fsp=6),
    nullable=False,
)
```

不要将 `fsp` 参数传给通用 `DateTime` 类型。

### 7.3 UUID

```python
import uuid

entity_id = str(uuid.uuid4())
```

### 7.4 多重用户关系

Request 分别关联 applicant、first_approver 和 second_approver。SQLAlchemy relationship 必须明确 `foreign_keys`，避免多个外键指向 users 时关系歧义。

### 7.5 Version

Request 模型可以配置 `version_id_col`，用于普通 ORM 对象更新的乐观锁检查。审批核心路径使用显式条件 UPDATE，因此必须自行在 WHERE 条件中包含 version，并检查 rowcount。

### 7.6 历史模型

历史表的字段必须完整包含操作类型、操作者、步骤、意见、操作前后状态和步骤、时间。业务层只提供新增和查询操作。

## 8. 查询规则

### 我发起的申请
过滤 `applicant_id = current_user_id`，可按 status 和 title keyword 筛选，分页返回 items、total、page、pageSize。

### 待我审批
只查询 `status = InProgress` 且当前步骤对应的审批人等于当前用户的申请：
- First：first_approver_id = current_user_id。
- Second：second_approver_id = current_user_id。

不能仅按审批人字段查询，否则会把已过期节点或已结束申请误列为待审批。

### 审批历史
按 `created_at ASC, id ASC` 排序，保证同一时间戳下的稳定顺序。

## 9. 事务与并发

提交、审批通过、审批驳回必须在同一个事务中更新 requests 并新增 approval_histories。

审批更新条件至少包含：
- id
- version
- 预期 status
- 预期 current_step
- 当前步骤对应的 approver_id

成功更新后 version 加一。rowcount 不为 1 时不得新增历史，返回状态冲突。历史写入失败时必须回滚申请状态和 version。

## 10. Alembic 迁移

迁移目录：`backend/migrations/`

常用命令：

```bash
uv run alembic revision --autogenerate -m "create initial tables"
uv run alembic upgrade head
alembic current
alembic history
uv run alembic downgrade -1
```

自动生成迁移后必须人工检查：
- 主键及外键
- 唯一索引及普通索引
- CHECK 约束
- 默认值
- 时间精度
- 字段长度和 NULL 属性

正式环境禁止以 `Base.metadata.create_all()` 代替 Alembic。

## 11. 数据库验收清单

- [ ] 三张表创建成功。
- [ ] 主键、外键和索引正确。
- [ ] username 唯一。
- [ ] 申请人不能是自己的审批人。
- [ ] 状态和步骤组合受约束。
- [ ] 历史关联正确。
- [ ] 历史排序稳定。
- [ ] Alembic 可在空数据库执行 upgrade head。
- [ ] 历史写入失败时业务事务回滚。
- [ ] 并发审批最多一个请求成功。


## 第一阶段实现补充（2026-11-24）

实际 MySQL 镜像为 8.4.7，表使用 utf8mb4_0900_as_cs（大小写敏感，包括 username 唯一性）。初始迁移 0001_initial 明确拒绝 InProgress + NULL，并限制历史 action 允许值。UUID、created_at、updated_at 在应用层生成 UTC 值；version 同时有数据库 DEFAULT 1。回退按 approval_histories → requests → users 删表，索引随表删除，避免删除外键依赖索引失败。
