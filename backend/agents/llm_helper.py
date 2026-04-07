import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def _api_key_ok() -> bool:
    k = (os.getenv("GROQ_API_KEY") or "").strip()
    return bool(k) and k.lower() != "dummy"


def get_llm(max_tokens: int = 500):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY", "dummy"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=max_tokens,
    )


def invoke_llm_text(
    prompt_template,
    variables: dict,
    timeout_sec: float = 8.0,
    max_tokens: int = 500,
) -> str:
    """
    Run LangChain chain in a thread with a wall-clock timeout so one slow LLM
    call cannot block the whole pipeline indefinitely.
    """
    if not _api_key_ok():
        raise RuntimeError("GROQ_API_KEY not configured")

    llm = get_llm(max_tokens=max_tokens)
    chain = prompt_template | llm

    def _run() -> str:
        return chain.invoke(variables).content.strip()

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_run)
        try:
            return fut.result(timeout=timeout_sec)
        except FuturesTimeout:
            raise TimeoutError(f"LLM call exceeded {timeout_sec}s")
