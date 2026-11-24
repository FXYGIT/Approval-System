# 07 — 开发记录（Development Log）

| 属性 | 内容 |
|---|---|
| 文档编号 | LOG-007 |
| 版本 | V1.0 |
| 状态 | 第五阶段完成 |

本文件记录实际开发进度与验证结果，只记录真实发生的工作。

## 开发计划跟踪

| 阶段 | 内容 | 状态 |
|---|---|---|
| 第一阶段 | 工程初始化（模型、迁移、Compose） | 完成 |
| 第二阶段 | 认证与申请草稿 | 完成 |
| 第三阶段 | 提交与两级审批 | 完成 |
| 第四阶段 | 前端认证与申请管理 | 完成 |
| 第五阶段 | 前端审批工作台与历史 | 完成 |

## 1. 第一阶段工程初始化（2026-11-24）

完成 User、Request、ApprovalHistory 模型；0001_initial 迁移；数据库健康检查；Vue 状态页；验收/开发 Compose；锁文件与运行文档。采用 src/app 布局、Vite、PyMySQL、MySQL 8.4.7（utf8mb4_0900_as_cs），运行镜像使用非 root 后端与 Nginx。环境：Windows + Docker Desktop Linux containers。

| 验证项 | 命令 / 操作 | 实际结果 |
|---|---|---|
| 验收模式 | docker compose up --build -d --wait | mysql/backend/frontend healthy；migrate Exited(0) |
| 迁移一致性 | alembic check / current | 无差异，0001_initial (head) |
| HTTP 冒烟 | :5173/、:5173/api/health、:8000/docs | 200，代理健康检查 database=ok |
| 前端类型/构建 | 镜像内 npm run build | 通过 |
| 数据库及健康接口测试 | README pytest 命令 | 20 passed |
| 开发模式与后端热更新 | 双 Compose 文件 up；更新时间戳 | 三服务 healthy；WatchFiles 重启成功 |
| 迁移往返 | 临时库 upgrade/downgrade/upgrade | 首次发现外键依赖索引不可先删，修为按依赖删表后通过 |
| 数据持久化 | 写探针、force-recreate mysql、读探针 | 数据保留 |
| 失败门禁 | 覆盖 migrate 命令退出 7，再 up backend | Compose 失败，backend 保持 Created 未启动 |

## 2. 第二阶段认证与申请草稿（2026-11-24）

实现注册、登录、JWT 认证、当前用户、分页用户候选、草稿创建/我的列表/详情/编辑/删除。API/Service/Repository 分层；Pydantic camelCase；统一异常与错误 Schema；申请人只由 JWT 确定；输入禁止客户端传身份与流程字段。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 完整测试 | README pytest 命令 | 82 passed |
| 安全覆盖 | JWT 过期/错误签名/算法/受众/签发者/类型/缺 exp/非法 sub/失效用户/未来 iat | 全部 401；弱/占位密钥启动失败 |
| 输入及权限 | 伪造身份/状态、未知字段、空白/超长、错误版本、跨用户读写删、非草稿 | HTTP 状态与数据库最终内容均符合契约 |
| 草稿一致性 | 编辑递增版本、相同内容编辑、旧版本更新、异常回滚 | 通过 |
| 读取后竞争 | 两条独立 Session 读取后变更 version/status | 旧条件 UPDATE/DELETE 返回 0 |
| 日志脱敏回归 | 复现原异常传播，增加 HTTP 中间件 | 修复后响应 500 且无敏感日志/堆栈 |
| OpenAPI | 检查所有业务路由 security、422 Schema、输入额外字段、输出脱敏 | 通过 |
| 实际 HTTP 链路 | Nginx → FastAPI → MySQL 全接口 | 通过，测试数据已清理 |

## 3. 第三阶段提交与两级审批（2026-11-24）

实现提交、一级/二级通过/驳回、审批历史、scope=pending 待审批列表；完成 Draft→InProgress→Approved/Rejected 全流转。申请人只由 JWT 确定；仅当前节点审批人可操作；状态更新与历史同一事务；Version 乐观锁条件 UPDATE 防重复与并发。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 提交与状态流转 | README pytest 命令 | 各动作与历史写入均符合状态机 |
| 权限区分 | 申请人/非当前节点审批人操作 | 403 APPROVAL_NOT_ASSIGNED；已结束或草稿 409 |
| 历史一致性 | 通过/驳回后历史 action 与 operator | 按 createdAt ASC、id ASC 排序 |
| 事务回滚 | monkeypatch 历史写入抛异常 | 状态回滚、version 不变、无多余历史 |
| 并发竞争 | 两条独立 Session 同时审批 | 仅一条 rowcount=1，version 只递增一次 |
| 待审批列表 | scope=pending 过滤 | 仅当前节点审批人可见 |
| 完整测试 / 静态验证 | pytest；ruff check/format | 103 passed；43 文件格式合规 |

## 4. 第四阶段前端认证与申请管理（2026-11-24）

实现前端基础架构（Vue Router、Pinia、Axios 封装、JWT 持久化、统一异常处理）与申请管理页面（我的申请列表、创建、草稿编辑/删除、详情）。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 前端组件测试 | npx vitest run | 15 passed |
| 类型检查 + 构建 | npm run build | 通过 |
| 生产镜像 | docker compose build frontend | 构建成功 |
| 端到端生命周期 | 经 :5173/api 注册→登录→me→用户列表→草稿 CRUD→404 | 全部通过，中文 UTF-8 正确 |
| 401 统一处理 | 无/失效 token 请求 /api/users/me | 401，拦截器转 ApiError 并触发登出 |

## 5. 第五阶段前端审批工作台与历史（2026-11-24）

实现待我审批列表、审批操作（一级/二级通过/驳回，动态权限）、审批历史时间线、草稿提交入口。通过意见可空、驳回意见必填；审批成功刷新；409/403 分别提示并刷新。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 组件/交互测试 | npx vitest run | 28 passed（新增 ApprovalHistory 4、ApprovalActions 9） |
| 类型检查 + 构建 | npm run build | 通过 |
| 生产镜像 | docker compose build frontend | 构建成功 |
| 后端环境 | docker compose up -d --build backend migrate | 审批路由生效，backend healthy |
| 端到端闭环 | 经 :5173/api | 提交→一级通过→二级通过→已通过；一级驳回；pending 过滤；403/409/422 守卫；历史轨迹正确 |

限制：浏览器 UI 人工交互未逐项验收，已通过组件单测、类型检查、生产构建与 HTTP 链路验证覆盖核心逻辑。
