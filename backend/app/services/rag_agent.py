"""RAG 问答 Agent 服务"""
import json
import httpx
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.config import settings
from app.models.policy import Policy, PolicyMetadata, PolicyChunk
from app.models.user import User
from app.services.embedding_service import EmbeddingService


class RAGAgent:
    """基于 RAG 的智能问答 Agent"""

    def __init__(self, db: AsyncSession, student: User):
        self.db = db
        self.student = student
        self.embedding = EmbeddingService()

    async def ask(self, question: str, history: list[dict] = None) -> dict:
        """处理用户问题，返回回答"""
        # 1. 检索相关段落
        relevant_chunks = await self._retrieve(question)

        # 2. 构建上下文
        context = self._build_context(relevant_chunks)

        # 3. 调用 LLM 生成回答
        answer = await self._generate(question, context, history or [])

        # 4. 提取来源
        sources = self._extract_sources(relevant_chunks)

        return {
            "answer": answer,
            "sources": sources,
            "chunks_count": len(relevant_chunks),
        }

    async def _retrieve(self, question: str, top_k: int = 5) -> list[dict]:
        """检索相关段落（语义检索 + 关键词降级）"""
        try:
            query_vector = await self.embedding.embed_text(question)
            vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

            sql = text("""
                SELECT pc.chunk_id, pc.chunk_content, pc.chunk_title,
                       pc.policy_id, p.title as policy_title,
                       1 - (pc.embedding <=> CAST(:query_vec AS vector)) as similarity
                FROM policy_chunks pc
                JOIN policies p ON pc.policy_id = p.policy_id
                WHERE p.status = 'published'
                  AND (p.department = :dept OR p.department = '全校')
                  AND (p.education_level = :edu OR p.education_level = '全校')
                  AND pc.embedding IS NOT NULL
                ORDER BY pc.embedding <=> CAST(:query_vec AS vector)
                LIMIT :limit
            """)
            result = await self.db.execute(sql, {
                "query_vec": vector_str, "dept": self.student.department,
                "edu": self.student.education_level or "本科", "limit": top_k,
            })
            rows = result.all()
            semantic_results = []
            for r in rows:
                sim = float(r[5]) if r[5] else 0
                if sim > 0.3:
                    semantic_results.append({
                        "chunk_id": r[0], "content": r[1],
                        "title": r[2] or "", "policy_id": r[3],
                        "policy_title": r[4], "similarity": sim,
                    })
            if semantic_results:
                return semantic_results
        except Exception as e:
            print(f"[Vector Search Error] {e}")
            await self.db.rollback()

        # 降级：关键词检索
        return await self._keyword_search(question, top_k)

    async def _keyword_search(self, question: str, top_k: int = 5) -> list[dict]:
        """关键词检索（降级方案）"""
        keywords = question.replace("?", "").replace("？", "").replace("的", "").replace("了", "").split()
        results = []

        for keyword in keywords[:3]:
            if len(keyword) < 2:
                continue
            result = await self.db.execute(
                select(PolicyChunk)
                .join(Policy, PolicyChunk.policy_id == Policy.policy_id)
                .where(
                    Policy.status == "published",
                    PolicyChunk.chunk_content.ilike(f"%{keyword}%"),
                    (Policy.department == self.student.department) | (Policy.department == "全校"),
                    (Policy.education_level == self.student.education_level) | (Policy.education_level == "全校"),
                )
                .limit(top_k)
            )
            for chunk in result.scalars().all():
                # 获取政策标题
                policy = await self.db.get(Policy, chunk.policy_id)
                results.append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.chunk_content,
                    "title": chunk.chunk_title or "",
                    "policy_id": chunk.policy_id,
                    "policy_title": policy.title if policy else "",
                    "similarity": 0.5,
                })
        return results[:top_k]

    def _build_context(self, chunks: list[dict]) -> str:
        """构建 LLM 上下文"""
        if not chunks:
            return "未找到相关文档。"

        context_parts = []
        for i, c in enumerate(chunks):
            section = f" ({c['title']})" if c['title'] else ""
            source = f"[来源: 《{c['policy_title']}》{section}]"
            context_parts.append(f"{c['content']}\n{source}")

        return "\n\n---\n\n".join(context_parts)

    def _extract_sources(self, chunks: list[dict]) -> list[dict]:
        """提取来源信息"""
        seen = set()
        sources = []
        for c in chunks:
            pid = c["policy_id"]
            key = f"{pid}-{c.get('title', '')}"
            if key not in seen:
                seen.add(key)
                section = f" ({c['title']})" if c['title'] else ""
                sources.append({
                    "policy_id": pid,
                    "title": c["policy_title"],
                    "section": section.strip(" ()") if c.get('title') else None,
                })
        return sources

    async def _generate(self, question: str, context: str, history: list[dict]) -> str:
        """调用 LLM 生成回答"""
        messages = [{"role": "system", "content": self._system_prompt()}]

        for h in history[-5:]:
            messages.append({"role": h["role"], "content": h["content"]})

        # 构建用户消息
        if context and context != "未找到相关文档。":
            user_content = f"""请根据以下资料回答问题。

相关资料：
{context}

问题：{question}

请基于资料回答，并标注来源（政策名称）。如果资料不足以回答，可以结合你的知识补充，但需说明哪些是资料中的、哪些是补充的。"""
        else:
            user_content = f"""问题：{question}

如果问题与校园政策、奖学金、申请相关，请诚实告知没有找到相关信息，建议联系辅导员。
如果是其他问题（如问候、自我介绍等），正常回答即可。"""
        messages.append({"role": "user", "content": user_content})

        # 调用 LLM
        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            return "AI 问答服务未配置（缺少 API Key），请联系管理员配置后使用。"

        api_url = (settings.DEEPSEEK_API_URL or "https://api.deepseek.com/v1").rstrip("/")
        api_url = f"{api_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 1000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI 服务暂时不可用，请稍后重试。错误：{str(e)[:100]}"

    def _system_prompt(self) -> str:
        """系统提示词"""
        return f"""你是一个校园政策问答助手，帮助{self.student.department}的学生解答问题。

规则：
1. 当有相关资料时，优先基于资料回答，并标注具体来源（政策名称 + 章节/段落）
2. 标注格式：引用处标注「来源：政策名称 - 章节名」
3. 当没有相关资料时，如果是政策相关问题，诚实告知"未找到相关信息，建议联系辅导员确认"
4. 如果是非政策问题（如问候、闲聊、自我介绍等），正常回答即可
5. 用中文回答，简洁清晰"""