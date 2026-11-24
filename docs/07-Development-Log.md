# 07 — 开发记录（Development Log）

| 属性 | 内容 |
|---|---|
| 文档编号 | LOG-007 |
| 版本 | V0.5 |
| 状态 | 第五阶段完成 |

## 1. 使用说明

本文件记录实际开发进度、技术决策变更、问题及验证结果。只记录真实发生的工作，不提前将计划标记为完成。

每条验证记录应注明：
- 日期
- 环境
- 命令或操作步骤
- 预期结果
- 实际结果
- 结论（通过 / 失败 / 未执行）

## 2. 初始项目决策

| 日期 | 决策 | 状态 |
|---|---|---|
| 2026-11-24 | 前端采用 Vue 3 + TypeScript | 已确认 |
| 2026-11-24 | 后端采用 Python FastAPI | 已确认 |
| 2026-11-24 | 数据库采用 MySQL | 已确认 |
| 2026-11-24 | ORM 采用 SQLAlchemy | 已确认 |
| 2026-11-24 | 后端使用 uv 管理 Python 项目 | 已确认 |
| 2026-11-24 | 使用同步 SQLAlchemy Session | 已确认 |
| 2026-11-24 | 使用 Alembic 管理迁移 | 已确认 |
| 2026-11-24 | 开发和验收均使用 Docker Compose | 已确认 |
| 2026-11-24 | Python 版本采用 3.12 | 已确认 |

## 3. 开发计划跟踪

| 阶段 | 计划内容 | 状态 | 证据 / 备注 |
|---|---|---|---|
| Day 1 | 需求、技术设计、ER 图、API、工程骨架 | 第一阶段完成 | 见第 8 节实际验证记录 |
| Day 2 | 注册登录、JWT、草稿功能 | 第二阶段完成 | 见第 9 节 |
| Day 3 | 提交、两级审批、详情及待审批 | 第三阶段完成 | 见第 10 节 |
| Day 4 | 驳回、历史、权限、事务、并发、测试 | 第三阶段完成 | 见第 10 节 |
| Day 5 | 前端认证与申请管理页面、组件测试与联调 | 第四阶段完成 | 见第 11 节 |
| Day 6 | 审批工作台、审批历史、审批操作与端到端联调 | 第五阶段完成 | 见第 12 节 |
| Day 7 | 全量验收、文档收尾与交付 | 未开始 | |

## 4. 技术问题与变更记录

| 日期 | 问题 / 变更 | 原因 | 影响文档 | 验证结果 |
|---|---|---|---|---|
| | | | | |

## 5. 测试与验收记录

| 日期 | 测试项 | 环境 / 命令 | 预期结果 | 实际结果 | 状态 |
|---|---|---|---|---|---|
| | | | | | 未执行 |

## 6. 遗留问题

| 编号 | 问题 | 优先级 | 负责人 | 计划处理时间 | 状态 |
|---|---|---|---|---|---|
| | | | | | 未处理 |

## 7. 每日收尾要求

每天结束前：
1. 更新当天完成项。
2. 记录未完成项和阻塞原因。
3. 记录重要技术决策及变更。
4. 记录测试命令和实际结果。
5. 确认文档与代码状态一致。

## 8. 第一阶段工程初始化（2026-11-24）

完成：User、Request、ApprovalHistory；0001_initial 迁移；FastAPI 数据库健康检查；Vue 3/TypeScript 状态页；根目录验收和开发 Compose；锁文件及运行文档。审批业务未实现。

实施选择：沿用 src/app 布局，使用 Vite、PyMySQL、MySQL 8.4.7；utf8mb4_0900_as_cs 区分大小写。运行镜像使用非 root 后端及 Nginx。

环境：Windows + Docker Desktop Linux containers，Docker Engine 28.3.0。

| 验证项 | 命令 / 操作 | 实际结果 |
|---|---|---|
| 验收模式 | docker compose up --build -d --wait | mysql/backend/frontend healthy；migrate Exited(0) |
| 迁移一致性 | docker compose exec backend alembic check / current | 无差异，0001_initial (head) |
| HTTP 冒烟 | GET :5173/、:5173/api/health、:8000/docs | 200，代理健康检查 database=ok |
| 前端类型/构建 | 镜像内 npm run build | vue-tsc + Vite 构建通过 |
| 数据库及健康接口测试 | README 中 pytest 命令 | 20 passed；覆盖合法/非法状态、NULL、大小写、版本、自审批、FK、用户名唯一、历史 action、503 |
| 开发模式 | 双 Compose 文件 up --build -d --wait | 三服务 healthy；Vite 源码请求与 API 代理通过 |
| 后端热更新 | 更新时间戳并查看日志 | WatchFiles 检测 main.py，工作进程重启成功 |
| 迁移往返 | 临时库 approval_migration_test：upgrade / downgrade base / upgrade / check | 初次发现外键依赖索引不可先删除；修为按依赖删表后通过 |
| 数据持久化 | 写探针、force-recreate mysql、读取探针 | 数据保留；探针已删除 |
| 失败门禁 | 临时覆盖 migrate 命令退出 7，再 up backend | Compose 失败，backend 保持 Created 未启动；随后恢复正常配置 |
| Python 静态检查 | uv lock --check；ruff check；ruff format --check | 通过，16 文件格式合规 |

限制：浏览器 HMR 交互未人工验收；已验证开发服务器挂载、源码响应和后端重载。首次 pytest 有第三方 TestClient/httpx 弃用提示及只读镜像缓存警告；README 的 cache_dir 参数避开缓存警告。未实现认证、审批、权限或并发业务测试。独立只读审查未发现其他阻塞缺陷。未执行 git commit/push。

## 9. 第二阶段认证与申请草稿（2026-11-24）

实现：注册、登录、JWT 身份认证、当前用户、分页用户候选列表、申请草稿创建/我的列表/详情/编辑/删除。API/Service/Repository 分层；Pydantic camelCase 输入输出；统一异常及错误 Schema。申请人只由 JWT 获取。输入禁止客户端传身份和流程字段。

边界：不实现提交、审批、历史查询、pending 列表和前端业务页面。未新增 Migration，数据库仍为 0001_initial。没有执行 Git commit/push。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 首轮失败测试 | Compose 测试容器，新增注册测试 | 原代码返回 404，确认接口尚不存在 |
| 完整测试 | README pytest 命令；最终源码测试 | 82 passed，1 条第三方 Starlette/httpx 弃用提示 |
| 安全覆盖 | JWT 过期、错误签名/算法/受众/签发者/类型、缺 exp、非法 sub、失效用户、未来 iat | 全部返回 401；弱/占位密钥启动失败 |
| 输入及权限 | 伪造身份/状态、未知字段、空白/超长、错误版本、跨用户读取/编辑/删除、非草稿 | HTTP 状态及数据库最终内容均符合契约 |
| 草稿一致性 | 编辑递增版本、相同内容编辑、旧版本更新、异常回滚、不生成历史 | 通过 |
| 读取后竞争 | 两条独立 MySQL Session，读取后变更 version/status | 旧条件 UPDATE/DELETE 返回 0，胜出内容保留 |
| 日志脱敏回归 | 先开启 TestClient 原异常传播复现，再增加 HTTP 中间件 | 原问题测试失败；修复后响应 500 且无原异常传播/敏感日志/堆栈 |
| OpenAPI | 自动化检查所有业务路由 security、422 Schema、输入额外字段与输出脱敏 | 通过 |
| 实际 HTTP 链路 | Nginx → FastAPI → MySQL：注册、登录、me、创建、列表、编辑、删除 | 全部通过；测试用户/草稿已清理 |
| 容器运行 | docker compose up --build -d --wait | 三个服务 healthy，migrate Exited(0) |
| 迁移一致性 | docker compose exec backend alembic check | No new upgrade operations detected |
| 静态验证 | uv lock --check、ruff check、ruff format --check | 通过，39 个 Python 文件格式合规 |

独立审查发现的日志异常传播问题已修复，读取后竞争测试已补齐；复核未发现遗留阻塞问题。测试数据以事务回滚为主，仅独立连接竞争和 HTTP 冒烟探针短暂提交并在 finally 中清理。

## 10. 第三阶段提交与两级审批（2026-11-24）

实现：申请提交、一级审批通过/驳回、二级审批通过/驳回、审批历史记录与查询，完成 Draft→InProgress→Approved/Rejected 全状态流转；新增 scope=pending 待审批列表。申请人只由 JWT 确定；仅当前节点指定审批人可操作。状态更新与历史写入同一事务；Version 乐观锁条件 UPDATE 防重复审批与并发冲突。

边界：本阶段不实现前端页面，未新增 Migration（复用 0001_initial 的 requests 与 approval_histories 表）。无 Git commit/push。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 提交与状态流转 | README pytest 命令 | 提交、一级通过、二级通过、一级驳回、二级驳回、历史写入均符合状态机 |
| 权限区分 | 申请人/非当前节点审批人操作 | 403 APPROVAL_NOT_ASSIGNED；已结束或草稿 409 INVALID_REQUEST_STATE |
| 历史一致性 | 通过/驳回后历史 action 与 operator | Submit/FirstApprove/…按 createdAt ASC、id ASC 排序 |
| 事务回滚 | monkeypatch 历史写入抛异常 | 状态回滚到 InProgress/First，version 不变，无多余历史 |
| 并发竞争 | 两条独立 MySQL Session 读同一版本后同时审批 | 仅一条 rowcount=1，另一条返回 0；version 只递增一次 |
| 待审批列表 | scope=pending 过滤 | 仅当前节点审批人可见，跨节点与已结束申请不可见 |
| 完整测试 | README pytest 命令 | 103 passed，1 条第三方 Starlette/httpx 弃用提示 |
| 静态验证 | ruff check、ruff format --check | 通过，43 个 Python 文件格式合规 |

## 11. 第四阶段前端认证与申请管理（2026-11-24）

实现：Vue 3 + TypeScript 前端基础架构——Vue Router 路由、Pinia 状态管理、Axios 请求封装、JWT Token 持久化与统一异常处理；注册、登录、退出登录、登录状态持久化；申请管理页面——我的申请列表（分页）、申请创建、草稿编辑、草稿删除、申请详情，接入后端接口正确展示状态、审批人与内容，处理加载/表单校验/空数据/错误反馈。

边界：本阶段不实现审批操作页面（审批工作台与审批历史留待下一阶段）。未新增 Migration。前端无 Git commit/push（与后端一致，后续统一提交）。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 前端组件测试 | npx vitest run | 15 passed（http 拦截器、auth store、RequestStatusTag、format） |
| 类型检查 + 构建 | npm run build | vue-tsc --noEmit + Vite 构建通过；仅 chunk >500 kB 提示 |
| 生产镜像 | docker compose build frontend | nginx-unprivileged 镜像构建成功 |
| 代理与健康 | 浏览器入口 :5173/ 与 :5173/api/health | 200；经前端代理 database=ok |
| 端到端生命周期 | Python urllib 经 :5173/api 走注册→登录→me→用户列表→草稿创建/列表/详情/编辑/删除→404 | 全部通过；中文内容 UTF-8 正确 |
| 401 统一处理 | 无/失效 token 请求 /api/users/me | 401 AUTHENTICATION_REQUIRED，前端拦截器转 ApiError 并触发登出 |

限制：浏览器 UI 人工交互（点击、表单校验提示、空态视觉）未逐项人工验收；已通过组件单测、类型检查、生产构建与 HTTP 链路验证覆盖核心逻辑。未实现审批工作台与历史页面。未执行 git commit/push。

## 12. 第五阶段前端审批工作台与审批历史（2026-11-24）

实现：待我审批列表（接入 scope=pending、分页、标题搜索、状态/审批步骤展示）；申请审批详情操作区——一级/二级通过与驳回，按当前用户身份、申请状态与审批节点动态控制操作权限；审批历史时间线组件，按时间顺序展示提交人、审批人、操作类型、意见与状态流转；草稿提交入口打通「提交→审批」闭环。审批通过意见可空、驳回意见必填；审批成功刷新数据；按钮 loading 防重复提交；409 并发冲突与 403 权限错误分别提示并刷新。

边界：本阶段不新增后端接口（复用第三阶段审批 API），未新增 Migration。后端运行环境重建为包含审批路由的镜像。前端无 Git commit/push（后续统一提交）。

| 验证项 | 环境 / 命令 | 实际结果 |
|---|---|---|
| 组件/交互测试 | npx vitest run | 28 passed（新增 ApprovalHistory 4、ApprovalActions 9） |
| 类型检查 + 构建 | npm run build | vue-tsc --noEmit + Vite 构建通过；仅 chunk >500 kB 提示 |
| 生产镜像 | docker compose build frontend | nginx-unprivileged 镜像构建成功 |
| 后端环境 | docker compose up -d --build backend migrate | 审批路由生效，migrate Exited(0)，backend healthy |
| 端到端闭环 | Python urllib 经 :5173/api | 提交→一级通过→二级通过→已通过；一级驳回→已驳回；pending 过滤；申请人审批 403、重复/过期审批 409、空驳回意见 422；历史轨迹 Submit/FirstApprove/SecondApprove、Submit/FirstReject 均正确 |

限制：浏览器 UI 人工交互（点击、对话框、空态视觉）未逐项人工验收；已通过组件单测、类型检查、生产构建与 HTTP 链路验证覆盖审批操作逻辑。未执行 git commit/push。
