# 04 — API 接口设计（API Design）

| 属性 | 内容 |
|---|---|
| 文档编号 | API-004 |
| 版本 | V0.3 |
| API 前缀 | `/api` |
| 认证方式 | JWT Bearer |

> 本文档是接口契约初稿。路由能力来自项目任务书；请求字段和响应结构为建议约定，实施前应结合 Pydantic Schema 和 OpenAPI 冻结。

## 1. 通用约定

- 使用 JSON 请求和响应。
- 业务接口除注册、登录外均需 JWT Bearer。
- 当前用户从 Token 解析，不接受客户端指定操作者身份。
- 资源 ID 使用 UUID 字符串。
- 时间使用 ISO 8601 格式。
- 分页默认 page=1、pageSize=10，最大 pageSize=100。

## 2. 接口清单

### 2.1 认证与用户

| Method | Path | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 否 | 注册 |
| POST | `/api/auth/login` | 否 | 登录并获取 JWT |
| GET | `/api/users/me` | 是 | 当前用户信息 |
| GET | `/api/users` | 是 | 用户简要列表，供选择审批人 |

### 2.2 申请管理

| Method | Path | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/requests` | 是 | 创建草稿 |
| GET | `/api/requests` | 是 | 分页查询 |
| GET | `/api/requests/{id}` | 是 | 申请详情 |
| PUT | `/api/requests/{id}` | 是 | 编辑草稿 |
| DELETE | `/api/requests/{id}` | 是 | 删除草稿 |

### 2.3 审批

| Method | Path | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/requests/{id}/submit` | 是 | 提交申请 |
| POST | `/api/requests/{id}/approve` | 是 | 当前节点通过 |
| POST | `/api/requests/{id}/reject` | 是 | 当前节点驳回 |
| GET | `/api/requests/{id}/history` | 是 | 审批历史 |

## 3. 请求模型建议

### 3.1 注册

`POST /api/auth/register`

```json
{
  "username": "alice",
  "password": "example-password",
  "displayName": "Alice"
}
```

用户名最长 50 字符，显示名称最长 100 字符。密码长度策略需在安全规范中确认。

### 3.2 登录

`POST /api/auth/login`

```json
{
  "username": "alice",
  "password": "example-password"
}
```

成功响应建议：

```json
{
  "accessToken": "<jwt>",
  "tokenType": "Bearer",
  "expiresIn": 3600
}
```

具体 Token 字段名和过期时间应在实现前冻结。

### 3.3 创建申请

`POST /api/requests`

```json
{
  "title": "采购申请",
  "content": "申请采购办公用品",
  "firstApproverId": "uuid-1",
  "secondApproverId": "uuid-2"
}
```

申请人由当前 Token 确定。创建后状态为 Draft，version 初始为 1。

### 3.4 编辑草稿

`PUT /api/requests/{id}`

```json
{
  "title": "修改后的标题",
  "content": "修改后的内容",
  "firstApproverId": "uuid-1",
  "secondApproverId": "uuid-2",
  "version": 1
}
```

version 用于草稿编辑的乐观锁。只有申请人可编辑自己的 Draft。

### 3.5 提交申请

`POST /api/requests/{id}/submit`

请求体可为空。后端根据数据库中的申请人、状态、审批人和版本进行验证。不得信任客户端传入 currentStep。

### 3.6 审批通过

`POST /api/requests/{id}/approve`

```json
{
  "comment": "同意",
  "version": 2
}
```

comment 可为空。version 可作为客户端观察到的版本提示；后端仍必须重新读取或条件更新数据库当前版本，不能仅依赖客户端值完成授权。

### 3.7 审批驳回

`POST /api/requests/{id}/reject`

```json
{
  "comment": "申请材料不完整",
  "version": 2
}
```

comment 必填，最长 500 字符。只允许当前节点指定审批人驳回。

## 4. 列表查询

`GET /api/requests`

支持参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| scope | string | mine 或 pending |
| page | integer | 页码，默认 1 |
| pageSize | integer | 每页数量，默认 10，最大 100 |
| status | string | 可选状态筛选 |
| keyword | string | 标题关键词 |

mine 仅查询当前用户发起的申请。

pending 仅查询当前用户在当前审批步骤需要处理的申请。

响应建议：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "pageSize": 10
}
```

## 5. 详情与历史

详情至少返回：
- 申请单基本信息
- 申请人
- 一级审批人
- 二级审批人
- 当前状态
- 当前步骤
- 当前审批人（若处于审批中）
- version
- 创建、更新和提交时间

历史按 `createdAt ASC, id ASC` 返回，至少包含操作类型、操作人、步骤、意见、前后状态 / 步骤和时间。

申请详情和历史均需验证当前用户是否为申请人或指定审批人之一。

## 6. 通用响应与错误

响应结构建议统一，但具体字段需最终冻结。例如：

```json
{
  "data": {},
  "message": "success"
}
```

错误响应建议：

```json
{
  "error": {
    "code": "APPROVAL_CONFLICT",
    "message": "申请状态已发生变化，请刷新后重试"
  }
}
```

HTTP 状态码：
- 200：成功
- 201：创建成功
- 400：业务参数错误
- 401：未登录或认证失败
- 403：无权限
- 404：资源不存在
- 409：状态冲突、重复审批或并发冲突
- 422：FastAPI 参数校验错误（若统一映射为 400，必须全项目保持一致）
- 500：未预期服务器错误

不得向客户端返回堆栈、SQL、密码哈希或密钥。

## 7. 业务错误码建议

| 错误码 | 含义 |
|---|---|
| USERNAME_ALREADY_EXISTS | 用户名已存在 |
| INVALID_CREDENTIALS | 用户名或密码错误 |
| REQUEST_NOT_FOUND | 申请不存在 |
| REQUEST_FORBIDDEN | 无权访问申请 |
| INVALID_REQUEST_STATE | 当前申请状态不允许此操作 |
| APPROVAL_NOT_ASSIGNED | 当前用户不是指定审批人 |
| APPROVAL_CONFLICT | 申请已被其他请求处理 |
| REJECTION_COMMENT_REQUIRED | 驳回意见必填 |
| INVALID_APPROVER | 审批人不存在或不合法 |

错误码为建议值，最终实现应与统一异常处理保持一致。

## 8. OpenAPI

FastAPI 自动生成：
- Swagger UI：`/docs`
- ReDoc：`/redoc`
- OpenAPI JSON：`/openapi.json`

所有接口应添加清晰的 summary、描述、请求模型、响应模型和可能的错误响应。

## 9. API 验收

- [ ] 注册和登录成功。
- [ ] 未携带 Token 的业务请求返回 401。
- [ ] 申请人由 Token 确定。
- [ ] 申请详情和历史执行权限校验。
- [ ] mine / pending 查询范围正确。
- [ ] 分页返回 total。
- [ ] 驳回意见必填。
- [ ] 重复或过期审批返回 409。
- [ ] OpenAPI 文档与实际接口一致。
