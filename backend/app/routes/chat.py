import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.providers.registry import registry
from app.services.key_store import key_store
from app.services.project_analyzer import analyze_for_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    project_path: str | None = None
    provider: str
    model: str
    history: list[ChatMessage] = []


class CreateIssueRequest(BaseModel):
    owner: str
    repo: str
    title: str
    body: str


@router.post("")
async def chat(req: ChatRequest):
    """Send a message to the LLM with optional project context."""
    provider = registry.get_provider(req.provider)
    api_key = key_store.get_key(req.provider)
    if api_key and hasattr(provider, "set_api_key"):
        provider.set_api_key(api_key)

    system_content = "You are a helpful code assistant. Answer questions about the codebase clearly and concisely."
    if req.project_path:
        try:
            context = analyze_for_context(req.project_path)
            system_content += f"\n\nHere is an overview of the project:\n{context}"
        except Exception as e:
            logger.warning("Failed to analyze project for chat: %s", e)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    for msg in req.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.message})

    try:
        reply = await provider.generate(messages, req.model)
    except Exception as e:
        logger.error("Chat LLM error: %s", e)
        raise HTTPException(502, f"LLM error: {e}")

    return {"reply": reply}


@router.post("/create-issue")
async def create_issue(req: CreateIssueRequest):
    """Create a GitHub issue on a public repository."""
    url = f"https://api.github.com/repos/{req.owner}/{req.repo}/issues"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"title": req.title, "body": req.body},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API error creating issue: %s", e)
        raise HTTPException(e.response.status_code, f"GitHub API error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.warning("GitHub API request failed: %s", e)
        raise HTTPException(502, "Failed to reach GitHub API")

    data = resp.json()
    return {"number": data["number"], "url": data["html_url"]}
