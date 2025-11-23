from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.langchain_chat import generate_chat_response, stream_chat_response


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    model_name: str | None = None


class ChatResponse(BaseModel):
    reply: str


@router.post("/completion", response_model=ChatResponse)
async def chat_completion(payload: ChatRequest) -> ChatResponse:
    """Simple chat completion endpoint using LangChain + LLM backend.

    You can extend this handler or add new ones in this module or new modules
    under `app/api/v1/endpoints`.
    """
    try:
        reply_text = await generate_chat_response(
            message=payload.message,
            model_name=payload.model_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="LLM backend error") from exc

    return ChatResponse(reply=reply_text)


@router.post("/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """Stream chat response as SSE so that frontend can consume it incrementally."""

    async def event_generator():  # type: ignore[return-type]
        try:
            async for chunk in stream_chat_response(
                message=payload.message,
                model_name=payload.model_name,
            ):
                # print(f"data: {chunk}\n\n")
                # Standard SSE format: 'data: <content>\n\n'
                yield f"data: {chunk}\n\n"
        except ValueError as exc:
            yield f"event: error\ndata: {str(exc)}\n\n"
        except Exception:
            yield "event: error\ndata: LLM backend error\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
