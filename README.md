# mxy-python

基于 **FastAPI + LangChain 1.x + DeepSeek** 的后端模板项目，支持快速扩展接口，并提供 Docker 部署示例。

## 功能概览

- FastAPI 构建 RESTful API
- LangChain 1.x 集成，示例聊天接口
- 配置集中在 `app/core/settings.py`，支持 `.env`
- Docker 镜像构建与运行示例

## 目录结构

```bash
mxy-python/
  ├── app/
  │   ├── api/
  │   │   └── v1/
  │   │       ├── __init__.py
  │   │       ├── router.py
  │   │       └── endpoints/
  │   │           └── chat.py
  │   ├── core/
  │   │   └── settings.py
  │   ├── services/
  │   │   └── langchain_chat.py
  │   ├── __init__.py
  │   └── main.py
  ├── requirements.txt
  ├── Dockerfile
  ├── .env.example
  └── README.md
```

## 本地运行

1. 创建并填写环境变量文件：

```bash
cp .env.example .env
# 编辑 .env 设置 DEEPSEEK_API_KEY 等
```

2. 安装依赖并启动：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3. 访问接口文档：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 示例接口：聊天补全（DeepSeek）

- URL: `POST /api/v1/chat/completion`
- 请求体：

```json
{
  "message": "你好，帮我介绍一下这个项目",
  "model_name": "deepseek-chat"
}
```

- 返回体示例：

```json
{
  "reply": "这里是基于 FastAPI 和 LangChain 构建的后端模板..."
}
```

## 扩展后端接口

- 在 `app/api/v1/endpoints/` 目录下新增 `xxx.py` 文件
- 在文件中定义 `APIRouter` 和接口函数
- 在 `app/api/v1/router.py` 中通过 `include_router` 挂载新的路由

示例（伪代码）：

```python
# app/api/v1/endpoints/ping.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"message": "pong"}
```

```python
# app/api/v1/router.py
from app.api.v1.endpoints import ping

api_router.include_router(ping.router, prefix="/utils", tags=["utils"])
```

## 使用 Docker 运行

1. 构建镜像：

```bash
docker build -t mxy-python:latest .
```

2. 运行容器（加载本地 .env）：

```bash
docker run --env-file .env -p 8000:8000 mxy-python:latest
```

然后访问：http://127.0.0.1:8000/docs

---

你可以根据自己的业务在 `services/` 和 `endpoints/` 中自由扩展逻辑，如果需要，我可以继续帮你设计更多链路或集成其他模型/向量数据库。
