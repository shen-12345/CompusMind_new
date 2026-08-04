from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.rag_agent import RAGAgent
from app.utils.response import success, error

router = APIRouter(prefix="/agent", tags=["智能问答"])


@router.post("/ask")
async def ask_question(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能问答"""
    body = await request.json()
    question = body.get("question", "")
    history = body.get("history", [])

    if not question.strip():
        return error(message="请输入问题")

    agent = RAGAgent(db, current_user)
    try:
        result = await agent.ask(question, history)
        return success(data=result)
    except Exception as e:
        return error(message=f"问答服务异常: {str(e)[:100]}")


@router.post("/reindex")
async def reindex_embeddings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重新生成所有切片的向量索引（仅 super_admin）"""
    if current_user.role != "super_admin":
        return error(message="仅超级管理员可操作")

    from app.models.policy import PolicyChunk
    from sqlalchemy import select
    from app.services.embedding_service import EmbeddingService

    result = await db.execute(select(PolicyChunk).where(PolicyChunk.embedding.is_(None)))
    chunks = result.scalars().all()

    if not chunks:
        return success(data={"message": "没有需要索引的切片"})

    embedding = EmbeddingService()
    count = 0
    for chunk in chunks:
        vec = await embedding.embed_text(chunk.chunk_content)
        chunk.embedding = vec
        count += 1
        if count % 5 == 0:
            await db.commit()

    await db.commit()
    return success(data={"indexed": count, "total": len(chunks)})