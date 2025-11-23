from typing import AsyncIterator, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.core.settings import settings


def _build_chain(model_name: Optional[str] = None) -> RunnableSerializable:
    """Build a simple LangChain pipeline.

    You can freely extend or replace this chain for more complex workflows.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", settings.system_prompt),
            ("human", "{input}"),
        ]
    )

    llm_model_name = model_name or settings.deepseek_model

    llm = ChatOpenAI(
        model=llm_model_name,
        temperature=settings.deepseek_temperature,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    chain = prompt | llm | StrOutputParser()
    return chain


async def generate_chat_response(message: str, model_name: Optional[str] = None) -> str:
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured")

    chain = _build_chain(model_name=model_name)

    # LangChain runnables support both sync and async
    result = await chain.ainvoke({"input": message})
    print(result)
    return result


async def stream_chat_response(message: str, model_name: Optional[str] = None) -> AsyncIterator[str]:
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured")

    chain = _build_chain(model_name=model_name)

    async for chunk in chain.astream({"input": message}):
        if chunk:
            yield str(chunk)
