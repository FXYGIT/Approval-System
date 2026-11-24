# 简易审批流系统

> 固定两级串行审批的前后端分离应用。项目处于初始设计阶段，本文档作为项目入口和运行说明。

## 1. 项目简介

系统支持员工创建申请、提交申请、由指定的一级和二级审批人依次处理，并查看申请状态及审批历史。

本期只实现固定两级串行审批，不实现通用工作流引擎。

## 2. 技术栈

| 模块 | 技术 | 决策状态 |
|---|---|---|
| 前端 | Vue 3 + TypeScript | 已确定 |
| 前端构建 | Vite | 建议采用 |
| 前端路由 | Vue Router | 建议采用 |
| 状态管理 | Pinia | 建议采用 |
| UI 组件 | Element Plus | 待确认 |
| 后端 | Python 3.12 + FastAPI | 已确定 |
| Python 依赖管理 | uv | 已确定 |
| ORM | SQLAlchemy 2.x，同步 Session | 已确定 |
| 数据库 | MySQL | 已确定 |
| 数据库驱动 | PyMySQL | 建议采用 |
| 数据库迁移 | Alembic | 已确定 |
| 身份认证 | JWT Bearer | 需求要求 |
| 密码哈希 | Argon2 | 建议采用 |
| 容器 | Docker Compose | 已确定 |

具体版本应通过依赖锁文件和镜像标签固定。MySQL 小版本、JWT 有效期、前端 UI 组件等仍应在开发前确认。

## 3. 仓库结构

```text
approval-system/
├── README.md
├── backend/
├── frontend/
├── docs/
│   ├── 01-Project-Spec.md
│   ├── 02-System-Architecture.md
│   ├── 03-Database-Design.md
│   ├── 04-API-Design.md
│   ├── 05-Development-Standards.md
│   ├── 06-Deployment-Guide.md
│   └── 07-Development-Log.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── .gitignore
```

## 4. 文档导航

| 文档 | 说明 |
|---|---|
| [需求与范围定义](docs/01-Project-Spec.md) | 需求来源、范围、角色、权限、流程及验收标准 |
| [系统架构设计](docs/02-System-Architecture.md) | 技术架构、模块边界、事务及并发策略 |
| [数据库设计](docs/03-Database-Design.md) | ER 图、表结构、约束、索引、ORM 和迁移 |
| [API 接口设计](docs/04-API-Design.md) | 接口清单、请求响应约定及错误处理 |
| [开发规范](docs/05-Development-Standards.md) | 代码组织、命名、Git、测试及 AI 辅助开发规范 |
| [部署指南](docs/06-Deployment-Guide.md) | 环境变量、Docker Compose、启动和验收 |
| [开发记录](docs/07-Development-Log.md) | 进度、决策变更、验证结果和遗留问题 |

## 5. 本地运行

项目约定开发和验收均使用 Docker Compose。实际启动命令以 `docs/06-Deployment-Guide.md` 和仓库中的 Compose 文件为准。

首次启动前：

1. 安装 Docker Engine / Docker Desktop 和 Docker Compose 插件。
2. 复制 `.env.example` 为 `.env`。
3. 为数据库密码和 JWT 密钥设置本地安全值。
4. 按部署指南启动服务并执行 Alembic 迁移。

## 6. 服务入口（规划）

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:5173（开发模式）或验收模式配置的端口 |
| FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |

以上地址为建议默认值，最终以 Compose 端口映射为准。

## 7. 测试

后端测试使用 pytest。测试命令、测试数据库配置及集成测试要求见 [开发规范](docs/05-Development-Standards.md) 和 [部署指南](docs/06-Deployment-Guide.md)。

## 8. 项目状态

当前为需求和技术设计阶段。文档中的“已确定”代表已确认的项目选型；“建议”或“待确认”内容必须在实施前评审，不应误认为已完成实现。

## 9. 交付物

- 前端源代码
- 后端源代码
- 数据库 Alembic 迁移
- Docker Compose 配置
- 自动化测试及测试结果
- 本 README 及 `docs/` 下项目文档
