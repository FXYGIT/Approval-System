# 05 — 开发规范（Development Standards）

| 属性 | 内容 |
|---|---|
| 文档编号 | DEV-005 |
| 版本 | V0.3 |
| 状态 | 初稿 |

## 1. 通用原则

- 代码优先清晰、可读、可测试。
- 业务规则由后端实现。
- 不在 Controller / Router 中堆积业务逻辑。
- 不提交真实密码、Token、密钥或敏感配置。
- 核心逻辑必须由开发者理解并能够解释。
- 文档随代码变化同步更新。

## 2. 前端规范

技术基线：Vue 3 + TypeScript。

建议目录：

```text
frontend/src/
├── api/
├── assets/
├── components/
├── layouts/
├── router/
├── stores/
├── types/
├── utils/
├── views/
├── App.vue
└── main.ts
```

约定：
- 使用 Composition API。
- 页面、公共组件、API 请求和类型定义分离。
- 所有 HTTP 请求通过统一 API 模块。
- 统一处理 JWT Header、错误响应和 Token 失效。
- 表单需进行前端校验，但后端必须重复校验关键业务条件。
- 页面需具备加载、空数据、成功和失败反馈。
- 使用 ESLint / Prettier（如采用，应提交配置并固定版本）。

## 3. 后端规范

技术基线：Python 3.12、FastAPI、uv、SQLAlchemy 2.x 同步 Session、Alembic。

建议目录：
- `api/`：HTTP 路由和依赖注入
- `core/`：配置、安全、异常、日志
- `db/`：Base 和 Session
- `models/`：ORM 模型
- `schemas/`：Pydantic 模型
- `repositories/`：数据访问
- `services/`：业务逻辑
- `tests/`：测试

依赖方向：API → Service → Repository → Session / Database。

Repository 不提交事务；Service 明确事务边界。每个请求使用独立 Session，结束后关闭。

## 4. Python 依赖管理

使用 uv 管理依赖和虚拟环境。提交 `pyproject.toml` 与 `uv.lock`。

常用命令：

```bash
uv sync --frozen
uv add fastapi "uvicorn[standard]" sqlalchemy pymysql alembic
uv add --dev pytest pytest-cov httpx ruff
uv lock
uv run pytest
uv run ruff check .
```

实际依赖应按代码使用情况添加，不安装无用依赖。建议使用 Argon2 密码哈希库；具体包及配置在安全实现时确认。

## 5. 命名规范

Python 遵循 PEP 8：
- 模块、函数、变量：snake_case
- 类：PascalCase
- 常量：UPPER_SNAKE_CASE

TypeScript：
- 组件使用 PascalCase。
- 变量和函数使用 camelCase。
- 类型和接口使用 PascalCase。

API 路径使用小写复数资源名，字段命名在 JSON 中统一使用 camelCase 或 snake_case，必须由 API 契约统一确定，前后端不得混用。

数据库表名和列名使用统一 snake_case。

## 6. Git 规范

提交格式：

```text
<type>: <description>
```

类型：
- feat：新功能
- fix：问题修复
- refactor：重构
- test：测试
- docs：文档
- chore：工程配置
- style：格式调整

示例：

```text
feat: add JWT authentication
feat: implement request submission
fix: prevent duplicate approval
test: add approval transaction tests
docs: update database design
chore: add docker compose
```

要求：
- 一个提交尽量对应一个清晰变更。
- 不在最后一天一次性提交所有代码。
- 提交前执行相关测试。
- 不提交 `.env`、密钥、本地虚拟环境、node_modules、构建产物和 IDE 缓存。
- `.gitignore` 必须覆盖前后端常见生成文件。

## 7. 测试规范

后端使用 pytest。关键业务测试应尽可能使用与验收一致的 MySQL，而不是仅用 SQLite 替代。

必须自动化测试：
1. 非当前审批人不能审批。
2. 一级审批通过后进入二级审批。
3. 历史写入失败时事务回滚。
4. 重复审批和并发审批最多一个成功。

建议另外覆盖：
- 注册、登录、JWT。
- 草稿创建、编辑和删除权限。
- 驳回意见必填。
- 二级审批结束。
- 无关用户无法查看申请。
- 分页及待审批列表。
- 状态非法组合。

测试应断言数据库最终状态和历史记录数量，不能只断言 HTTP 状态码。

## 8. AI 辅助开发规范

AI 生成内容不能直接视为完成。开发人员必须：
1. 阅读并理解生成代码。
2. 对照 Spec 核对业务规则。
3. 检查身份认证、权限和输入校验。
4. 检查事务和并发行为。
5. 执行自动化测试。
6. 验证异常路径。
7. 更新相关文档。

不得将未经验证的 AI 生成代码提交为已完成实现。

## 9. Code Review 检查项

- 是否遵守模块职责和依赖方向？
- 是否存在客户端可控的身份或审批步骤？
- 是否存在越权读取或操作？
- 状态变化是否符合状态机？
- 状态更新和历史写入是否处于同一事务？
- 并发更新是否检查版本和 rowcount？
- 是否记录敏感信息？
- 是否有对应测试？
- 文档是否与实现一致？

## 10. 完成定义（Definition of Done）

一个功能只有在以下条件满足后才能标记完成：
- 代码已实现并通过审查。
- 相关测试已运行并通过。
- 关键异常路径已验证。
- API / 数据库变更已更新文档和迁移。
- 不包含未解释的临时配置或敏感信息。
