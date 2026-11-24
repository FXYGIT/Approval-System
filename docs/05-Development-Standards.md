# 05 — 开发规范（Development Standards）

| 属性 | 内容 |
|---|---|
| 文档编号 | DEV-005 |
| 版本 | V1.0 |
| 状态 | 终稿 |

## 1. 通用原则

代码优先清晰、可读、可测试；业务规则由后端实现；不在 Router 堆积业务逻辑；不提交密码、Token、密钥或敏感配置；文档随代码同步更新。

## 2. 前端规范

技术栈 Vue 3 + TypeScript，Composition API。目录 `frontend/src/`：`api`（请求封装）、`components`、`layouts`、`router`、`stores`、`types`、`utils`、`views`。约定：页面/组件/API/类型分离；所有请求经统一 API 模块，集中处理 JWT Header、错误响应与 Token 失效；表单前端校验，后端重复校验关键条件；页面具备加载、空数据、成功/失败反馈。

## 3. 后端规范

技术栈 Python 3.12 + FastAPI + uv + SQLAlchemy 2.x 同步 Session + Alembic。目录 `backend/src/app/`：`api`、`core`、`db`、`models`、`schemas`、`repositories`、`services`。依赖方向 API → Service → Repository → Session/Database。Repository 不提交事务；Service 明确事务边界；每请求独立 Session，结束后关闭。

## 4. 命名规范

Python（PEP 8）：模块/函数/变量 snake_case，类 PascalCase，常量 UPPER_SNAKE_CASE。TypeScript：组件 PascalCase，变量/函数 camelCase，类型/接口 PascalCase。API 路径小写复数，JSON 字段统一 camelCase。数据库表名/列名 snake_case。

## 5. Git 规范

提交格式 `<type>: <description>`，type 取 feat/fix/refactor/test/docs/chore/style。一个提交对应一个清晰变更；提交前运行测试；不提交 `.env`、密钥、虚拟环境、node_modules、构建产物与 IDE 缓存；`.gitignore` 覆盖前后端生成文件。

## 6. 测试规范

后端 pytest，关键业务测试用与验收一致的 MySQL（非 SQLite）。必须自动化：非当前审批人不能审批、一级通过进入二级、历史写入失败回滚、重复/并发审批最多一个成功。另覆盖注册登录/JWT、草稿权限、驳回意见必填、二级审批结束、越权查看、分页与待审批列表、非法状态组合。断言数据库最终状态与历史数量，不只断言 HTTP 状态码。

## 7. AI 辅助开发规范

AI 生成内容不得直接视为完成。开发者须：阅读并理解生成代码、对照 Spec 核对业务规则、检查认证/权限/输入校验、检查事务与并发、执行测试、验证异常路径、更新文档。不得提交未经验证的 AI 生成代码。

## 8. Code Review 检查项

- 是否遵守模块职责与依赖方向？
- 是否存在客户端可控的身份或审批步骤？
- 是否越权读取或操作？
- 状态变化是否符合状态机？
- 状态更新与历史写入是否同一事务？
- 并发更新是否检查版本与 rowcount？
- 是否记录敏感信息？
- 是否有对应测试、文档与实现一致？

## 9. 完成定义（Definition of Done）

代码实现并通过审查；相关测试通过；关键异常路径已验证；API/数据库变更已更新文档与迁移；不含未解释的临时配置或敏感信息。
