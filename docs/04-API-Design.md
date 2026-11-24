# 04 — API 接口设计

版本：V0.5（第三阶段）。本文件记录当前实现契约；前端认证、草稿及审批页面仍为后续计划。运行时完整 Schema 见 `/openapi.json`，交互文档见 `/docs`。

## 通用契约

- API 前缀 `/api`，JSON 字段采用 camelCase；成功响应直接返回对象或分页对象，不加 data 包装。
- 注册、登录和健康检查公开；其余接口使用 `Authorization: Bearer <accessToken>`。
- UUID 字符串作为 ID；时间按 UTC 保存，响应 ISO 8601，带 `Z`。
- 输入模型禁止未知字段。applicantId、applicant_id、operatorId、status、currentStep 等身份或流程字段不可写入草稿请求体，传入返回 422。
- 密码 8–128 字符，保留首尾空格；用户名 1–50、显示名 1–100，去除首尾空格后不能为空。用户名区分大小写。
- JWT 固定 HS256，校验签名、exp、iat、UUID sub、issuer=approval-system、audience=approval-api、type=access，并查询用户仍然存在。默认有效期 60 分钟，可配置 1–1440 分钟；本阶段无刷新或撤销接口。
- 密码使用 Argon2id，只保存哈希；响应不包含密码或密码哈希。

## 当前接口

| 方法 | 路径 | 成功状态 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 201 | 注册，返回 UserPublic |
| POST | `/api/auth/login` | 200 | 登录，返回 TokenResponse |
| GET | `/api/users/me` | 200 | 当前用户，返回 UserPublic |
| GET | `/api/users` | 200 | 用户候选列表，返回 Page<UserSummary> |
| POST | `/api/requests` | 201 | 创建草稿，返回 RequestPublic |
| GET | `/api/requests` | 200 | 我发起的申请，返回 Page<RequestPublic> |
| GET | `/api/requests/{request_id}` | 200 | 申请详情 |
| PUT | `/api/requests/{request_id}` | 200 | 编辑自己的草稿 |
| DELETE | `/api/requests/{request_id}` | 204 | 删除自己的草稿，无响应体 |
| POST | `/api/requests/{request_id}/submit` | 200 | 提交申请，返回 RequestPublic |
| POST | `/api/requests/{request_id}/approve` | 200 | 当前节点审批通过，返回 RequestPublic |
| POST | `/api/requests/{request_id}/reject` | 200 | 当前节点审批驳回，返回 RequestPublic |
| GET | `/api/requests/{request_id}/history` | 200 | 审批历史，返回 list[HistoryEntry] |
| GET | `/api/health` | 200 | API 与数据库健康检查 |

### 注册与登录

注册：`{"username":"alice","password":"example-password","displayName":"Alice"}`。

登录：`{"username":"alice","password":"example-password"}`。

UserSummary：id、username、displayName。UserPublic 额外包含 createdAt。

TokenResponse：`{"accessToken":"<jwt>","tokenType":"Bearer","expiresIn":3600}`。

重复用户名返回 409；错误用户名与错误密码统一返回 401 INVALID_CREDENTIALS。Bearer 缺失、损坏、过期或用户不存在均返回 401，并携带 `WWW-Authenticate: Bearer`。

### 草稿创建与编辑

```json
{
  "title": "采购申请",
  "content": "申请采购办公用品",
  "firstApproverId": "有效用户 UUID",
  "secondApproverId": "有效用户 UUID"
}
```

标题 1–100 字符、内容 1–2000 字符，去除首尾空格后不能为空。两个审批人都必须存在且不能是申请人本人；两级审批人允许是同一用户。

创建时 applicantId 只取 JWT 当前用户，status=Draft、currentStep=null、version=1、submittedAt=null。

PUT 使用相同四个字段，额外必须携带正整数 version。只允许申请人编辑 Draft；过期版本返回 409 REQUEST_CONFLICT。成功编辑即使内容未变化也递增 version，并更新 updatedAt。

DELETE 只允许申请人删除 Draft；使用服务端读取的版本和 Draft 条件删除，读取后记录变化返回 409。创建、编辑、删除草稿都不生成审批历史。

RequestPublic 包含：id、title、content、applicantId、firstApproverId、secondApproverId、applicant/firstApprover/secondApprover（UserSummary）、status、currentStep、version、createdAt、updatedAt、submittedAt。

详情允许申请人或任一指定审批人查看，其他用户返回 403；不存在返回 404。审批人身份不赋予草稿编辑/删除权限。

### 列表

`GET /api/requests?scope=mine&page=1&pageSize=10&status=Draft&keyword=采购`

- scope 可选 mine（我发起的，默认）或 pending（待我审批）。
- page 为 1–1000000，pageSize 为 1–100，默认分别 1、10。
- status 仅对 scope=mine 生效，可选 Draft/InProgress/Approved/Rejected；keyword 最长 100，按标题字面子串匹配，% 和 _ 不作为通配符。
- scope=mine 返回当前用户发起的申请；scope=pending 返回 status=InProgress 且当前节点审批人为当前用户的申请（First 匹配 firstApproverId，Second 匹配 secondApproverId）。均按 createdAt DESC、id DESC 稳定排序。
- 返回 `{"items":[],"total":0,"page":1,"pageSize":10}`。

用户列表使用同样分页参数，keyword 最长 50，按 username 字面子串匹配，按 username、id 排序。仅登录用户可查询，返回 Page<UserSummary>。

### 提交与两级审批

提交 `POST /api/requests/{id}/submit`：仅申请人可提交 Draft；Draft→InProgress/First，version 递增并写 submittedAt，同时新增一条 Submit 历史。非申请人返回 403；非 Draft 返回 409 INVALID_REQUEST_STATE；读取后版本变化返回 409 APPROVAL_CONFLICT。

通过 `POST /api/requests/{id}/approve`，请求体 `{"comment":"同意","version":3}`：comment 可空、最长 500（去除首尾空格）；version 可选，为乐观锁前置条件。驳回 `POST /api/requests/{id}/reject`：comment 必填 1–500 字符（去除首尾空格），version 可选。

状态机：一级通过 First→Second；二级通过 Second→Approved；任一节点驳回 →Rejected。不允许跳节点、重复审批或审批已结束申请。不实现驳回后重提、撤回、会签、转交、动态审批人。一级/二级审批人可为同一人，但须分别完成两步。

权限：仅当前节点指定审批人可操作。非当前节点审批人返回 403 APPROVAL_NOT_ASSIGNED；申请已结束或为草稿返回 409 INVALID_REQUEST_STATE；版本过期或并发竞争返回 409 APPROVAL_CONFLICT。三者严格区分。

一致性：状态更新与历史新增在同一事务提交；审批用条件 UPDATE（WHERE 至少含 id、读取时 version、status、current_step、当前节点审批人），仅当影响行数为 1 才写历史，否则回滚并返回 409。

历史 `GET /api/requests/{id}/history`：仅申请人或任一指定审批人可读，其他用户 403；按 createdAt ASC、id ASC 稳定排序。HistoryEntry 含 id、action（Submit/FirstApprove/FirstReject/SecondApprove/SecondReject）、operator（UserSummary）、step、comment、previousStatus、previousStep、newStatus、newStep、createdAt。提交、通过、驳回各产生一条历史；删除草稿不产生历史。

## 错误格式

统一响应：`{"error":{"code":"REQUEST_FORBIDDEN","message":"无权查看该申请"}}`。

| HTTP | code | 场景 |
|---|---|---|
| 400 | INVALID_APPROVER | 审批人不存在或是申请人自己 |
| 401 | AUTHENTICATION_REQUIRED | 缺少有效 Bearer 认证头 |
| 401 | INVALID_TOKEN | Token 无效/过期/用户不存在 |
| 401 | INVALID_CREDENTIALS | 用户名或密码错误 |
| 403 | REQUEST_FORBIDDEN | 无权读取、修改申请或查看历史 |
| 403 | APPROVAL_NOT_ASSIGNED | 非当前节点的审批人操作 |
| 404 | REQUEST_NOT_FOUND | 申请不存在 |
| 409 | USERNAME_ALREADY_EXISTS | 用户名已存在 |
| 409 | INVALID_REQUEST_STATE | 修改/删除/提交/审批非当前状态 |
| 409 | REQUEST_CONFLICT | 草稿版本过期或读取后数据变化 |
| 409 | APPROVAL_CONFLICT | 审批版本过期或并发竞争 |
| 422 | VALIDATION_ERROR | 请求参数校验失败 |
| 500 | INTERNAL_ERROR | 未预期错误 |
| 503 | HTTP_503 | 数据库健康检查失败 |

路由级 404、405 等使用 HTTP_<状态码>。错误响应不回显请求体、密码、Token、SQL 或堆栈。

## 后续阶段（未实现）

前端认证、草稿管理及审批页面尚未实现；提交与两级审批的后端契约已按本节开放，审批并发控制已通过 Version 乐观锁与条件 UPDATE 完成。
