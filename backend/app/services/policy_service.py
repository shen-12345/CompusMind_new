import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.policy import Policy, PolicyMetadata, PolicyChunk
from app.core.config import settings


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "policies")


class PolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_policy(
        self, file_content: bytes, filename: str,
        department: str, education_level: str,
        applicable_grades: list, project_category: str,
        created_by: int,
    ) -> dict:
        """上传并解析政策文档"""
        # 校验文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".pdf", ".docx"):
            raise ValueError("仅支持 PDF 和 Word 格式")

        # 计算 MD5 检测重复（同一学院+同一分类下的相同文件才算重复）
        file_md5 = hashlib.md5(file_content).hexdigest()
        result = await self.db.execute(
            select(Policy).where(
                Policy.file_md5 == file_md5,
                Policy.department == department,
                Policy.project_category == project_category,
                Policy.education_level == education_level,
                Policy.status != "archived",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"该文档已上传过（{department} - {project_category} - {education_level}），请勿重复上传")

        # 解析文档内容
        text_content = self._parse_document(file_content, ext)

        # 创建政策记录
        policy = Policy(
            title=filename,
            content_full=text_content,
            department=department,
            education_level=education_level,
            applicable_grades=applicable_grades,
            project_category=project_category,
            status="draft",
            file_md5=file_md5,
            created_by=created_by,
        )
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)

        # 保存文件到磁盘
        os.makedirs(os.path.join(UPLOAD_DIR, str(policy.policy_id)), exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, str(policy.policy_id), f"original{ext}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 文本切片
        chunks = self._chunk_text(text_content)

        # 保存切片并生成向量
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()

        for i, chunk in enumerate(chunks):
            chunk_record = PolicyChunk(
                policy_id=policy.policy_id,
                chunk_content=chunk["content"],
                chunk_index=i,
                chunk_title=chunk.get("title", ""),
            )
            self.db.add(chunk_record)

        # 先提交以获取 chunk_id
        await self.db.flush()

        # 查询刚插入的 chunks 并生成向量
        from sqlalchemy import select
        result = await self.db.execute(
            select(PolicyChunk).where(PolicyChunk.policy_id == policy.policy_id).order_by(PolicyChunk.chunk_index)
        )
        saved_chunks = result.scalars().all()
        for chunk in saved_chunks:
            vec = await embedding_service.embed_text(chunk.chunk_content)
            chunk.embedding = vec

        await self.db.commit()

        return {
            "policy_id": policy.policy_id,
            "title": policy.title,
            "status": policy.status,
            "message": "上传成功，解析完成",
            "chunks_count": len(chunks),
            "text_length": len(text_content),
        }

    def _parse_document(self, content: bytes, ext: str) -> str:
        """解析文档内容为纯文本"""
        if ext == ".pdf":
            return self._parse_pdf(content)
        elif ext == ".docx":
            return self._parse_docx(content)
        return ""

    def _parse_pdf(self, content: bytes) -> str:
        """使用 PyMuPDF 解析 PDF"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            texts = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    texts.append(text)
            doc.close()
            return "\n\n".join(texts)
        except ImportError:
            return "PyMuPDF 未安装，请执行: pip install PyMuPDF"
        except Exception as e:
            return f"PDF 解析失败: {str(e)}"

    def _parse_docx(self, content: bytes) -> str:
        """使用 python-docx 解析 Word"""
        try:
            import docx
            from io import BytesIO
            doc = docx.Document(BytesIO(content))
            texts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    texts.append(para.text)
            return "\n\n".join(texts)
        except ImportError:
            return "python-docx 未安装，请执行: pip install python-docx"
        except Exception as e:
            return f"Word 解析失败: {str(e)}"

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> list[dict]:
        """将文本按段落切分为块"""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_title = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 尝试识别标题（短行，无句号结尾）
            is_title = len(para) < 50 and not para.endswith(("。", "？", "！", "；", "："))

            if is_title:
                current_title = para
                continue

            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({"content": current_chunk.strip(), "title": current_title})
                # overlap: 保留上一块末尾的部分内容
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n" + para
            else:
                current_chunk += "\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append({"content": current_chunk.strip(), "title": current_title})

        return chunks

    async def extract_metadata_with_llm(self, policy_id: int, text_content: str) -> dict:
        """调用 LLM 提取结构化字段"""
        # 构造 prompt
        prompt = f"""你是一个政策文档分析助手。请从以下政策通知文本中提取关键信息，以 JSON 格式返回。

必须提取的字段：
- project_name: 项目/政策名称
- deadline: 材料提交截止时间（格式：YYYY-MM-DD HH:mm）
- prerequisites: 硬性申请条件（数组，如无则留空数组）
- mutually_exclusive: 不可同时申请的项目（数组，如无则留空数组）
- material_list: 需要提交的材料清单（数组）
- review_process: 评选流程说明
- contact_info: 联系方式

政策文本：
{text_content[:8000]}

请直接返回 JSON，不要包含其他文字。
"""

        # 调用 LLM API
        llm_result = await self._call_llm(prompt)

        try:
            # 尝试解析 JSON
            extracted = json.loads(llm_result)
        except json.JSONDecodeError:
            # 如果 LLM 返回了 Markdown 代码块，尝试提取
            import re
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_result)
            if json_match:
                extracted = json.loads(json_match.group(1))
            else:
                raise ValueError("LLM 返回格式无法解析")

        # 检查是否已有元数据（有则更新，无则插入）
        existing_meta = await self.db.execute(
            select(PolicyMetadata).where(PolicyMetadata.policy_id == policy_id)
        )
        existing_meta = existing_meta.scalar_one_or_none()

        meta_data = {
            "project_name": extracted.get("project_name", "") or "未命名项目",
            "deadline": self._parse_deadline(extracted.get("deadline", "")),
            "prerequisites": extracted.get("prerequisites", []),
            "mutually_exclusive": extracted.get("mutually_exclusive", []),
            "material_list": extracted.get("material_list", []),
            "review_process": extracted.get("review_process", "") or "",
            "contact_info": extracted.get("contact_info", "") or "",
            "confidence_score": "0.85",
        }

        if existing_meta:
            for key, value in meta_data.items():
                setattr(existing_meta, key, value)
        else:
            metadata = PolicyMetadata(policy_id=policy_id, **meta_data)
            self.db.add(metadata)

        await self.db.commit()

        return extracted

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM API（DeepSeek / 通义千问）"""
        from app.core.config import settings
        api_key = settings.DEEPSEEK_API_KEY
        api_url = settings.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"

        if not api_key:
            # 如果没有配置 API key，返回模拟数据用于开发测试
            return json.dumps({
                "project_name": "示例奖学金项目",
                "deadline": "2026-09-20 17:00",
                "prerequisites": ["成绩排名前 30%", "无违纪记录"],
                "mutually_exclusive": ["不可与国家奖学金兼得"],
                "material_list": ["申请表", "成绩单", "导师推荐信"],
                "review_process": "学院推荐 → 学校评审 → 公示 5 个工作日",
                "contact_info": "张老师 010-12345678",
            }, ensure_ascii=False)

        try:
            import httpx
            # 确保 URL 包含 /chat/completions
            if not api_url.endswith("/chat/completions"):
                base = api_url.rstrip("/")
                api_url = f"{base}/chat/completions"

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            # 失败时返回模拟数据，让用户手动填写
            print(f"[LLM API Error] {type(e).__name__}: {str(e)[:200]}")
            return json.dumps({
                "project_name": "",
                "deadline": "",
                "prerequisites": [],
                "mutually_exclusive": [],
                "material_list": [],
                "review_process": "",
                "contact_info": "",
            }, ensure_ascii=False)

    def _parse_deadline(self, date_str: str) -> Optional[datetime]:
        """解析截止时间字符串"""
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    async def get_policy_list(
        self, page: int = 1, page_size: int = 20,
        status: str = None, department: str = None,
        created_by: int = None,
    ) -> tuple[list[Policy], int]:
        """获取政策列表"""
        query = select(Policy)
        count_query = select(func.count(Policy.policy_id))

        if status:
            query = query.where(Policy.status == status)
            count_query = count_query.where(Policy.status == status)
        if department:
            query = query.where(Policy.department == department)
            count_query = count_query.where(Policy.department == department)
        if created_by:
            query = query.where(Policy.created_by == created_by)
            count_query = count_query.where(Policy.created_by == created_by)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Policy.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        policies = result.scalars().all()

        return list(policies), total

    async def get_student_policies(
        self, student_department: str, student_education: str, student_grade: str,
        page: int = 1, page_size: int = 20,
    ) -> tuple[list[Policy], int]:
        """获取学生可见的政策列表（已发布 + 匹配学历/学院/年级）"""
        from sqlalchemy import or_

        query = select(Policy).where(
            Policy.status == "published",
            or_(
                Policy.department == student_department,
                Policy.department == "全校",
            ),
            or_(
                Policy.education_level == student_education,
                Policy.education_level == "全校",
            ),
        )
        count_query = select(func.count(Policy.policy_id)).where(
            Policy.status == "published",
            or_(
                Policy.department == student_department,
                Policy.department == "全校",
            ),
            or_(
                Policy.education_level == student_education,
                Policy.education_level == "全校",
            ),
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Policy.published_at.desc().nullslast())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        policies = result.scalars().all()

        return list(policies), total

    async def get_policy_detail(self, policy_id: int) -> Optional[dict]:
        """获取政策详情（含元数据）"""
        result = await self.db.execute(
            select(Policy).where(Policy.policy_id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            return None

        meta_result = await self.db.execute(
            select(PolicyMetadata).where(PolicyMetadata.policy_id == policy_id)
        )
        metadata = meta_result.scalar_one_or_none()

        return {"policy": policy, "metadata": metadata}

    async def publish_policy(self, policy_id: int, metadata_updates: dict = None) -> Policy:
        """发布政策"""
        result = await self.db.execute(
            select(Policy).where(Policy.policy_id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError("政策不存在")

        # 更新元数据（导员在预览页修改后的值）
        if metadata_updates:
            meta_result = await self.db.execute(
                select(PolicyMetadata).where(PolicyMetadata.policy_id == policy_id)
            )
            metadata = meta_result.scalar_one_or_none()
            if metadata:
                for key, value in metadata_updates.items():
                    if hasattr(metadata, key):
                        setattr(metadata, key, value)

        policy.status = "published"
        policy.published_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def withdraw_policy(self, policy_id: int) -> Policy:
        """撤回已发布的政策"""
        result = await self.db.execute(
            select(Policy).where(Policy.policy_id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError("政策不存在")
        if policy.status != "published":
            raise ValueError("只有已发布的政策才能撤回")
        policy.status = "draft"
        policy.published_at = None
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def delete_policy(self, policy_id: int) -> None:
        """删除草稿政策"""
        result = await self.db.execute(
            select(Policy).where(Policy.policy_id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError("政策不存在")
        if policy.status == "published":
            raise ValueError("已发布的政策不能删除，请先撤回")
        # 删除关联的切片和元数据
        await self.db.execute(
            select(PolicyChunk).where(PolicyChunk.policy_id == policy_id)
        )
        # 先删除 chunks
        from sqlalchemy import delete
        await self.db.execute(delete(PolicyChunk).where(PolicyChunk.policy_id == policy_id))
        await self.db.execute(delete(PolicyMetadata).where(PolicyMetadata.policy_id == policy_id))
        await self.db.execute(delete(Policy).where(Policy.policy_id == policy_id))
        await self.db.commit()