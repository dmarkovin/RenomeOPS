from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Document, User

async def create_document(
    name: str,
    doc_type: str,
    number: str = "",
    sender: str = "",
    recipient: str = "",
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None
) -> Document:
    async with AsyncSessionLocal() as db:
        doc = Document(
            name=name,
            doc_type=doc_type,
            number=number or None,
            sender=sender or None,
            recipient=recipient or None,
            comment=comment or "",
            photo_ids=photo_ids or [],
            created_by=created_by,
            status="active",
            comments=[],  # инициализируем пустым списком
            history=[]    # инициализируем пустым списком
        )
        db.add(doc)
        await db.flush()
        # Добавляем запись в историю
        _add_history(doc, "CREATED", created_by, "Документ создан")
        await db.commit()
        await db.refresh(doc)
        return doc

async def get_document(doc_id: int) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        return await db.get(Document, doc_id)

async def get_documents(
    doc_type: str = None,
    status: str = None,
    limit: int = 20,
    offset: int = 0
) -> List[Document]:
    async with AsyncSessionLocal() as db:
        query = select(Document).order_by(Document.created_at.desc())
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        if status:
            query = query.where(Document.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

async def update_document_status(doc_id: int, status: str) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return None
        old_status = doc.status
        doc.status = status
        doc.updated_at = datetime.now()
        # Добавляем историю
        _add_history(doc, "STATUS_CHANGE", None, f"Статус изменён с {old_status} на {status}")
        await db.commit()
        await db.refresh(doc)
        return doc

async def delete_document(doc_id: int) -> bool:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return False
        await db.delete(doc)
        await db.commit()
        return True

# ===== Функции для комментариев и истории =====

def _add_history(doc, action: str, user_id: int = None, details: str = ""):
    """Добавляет запись в историю документа"""
    if doc.history is None:
        doc.history = []
    entry = {
        "action": action,
        "user_id": user_id,
        "user_name": None,  # можно будет подставить при отображении
        "details": details,
        "created_at": datetime.now().isoformat()
    }
    doc.history.append(entry)

async def add_document_comment(doc_id: int, user_id: int, author_name: str, text: str) -> bool:
    """Добавляет комментарий к документу"""
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return False
        if doc.comments is None:
            doc.comments = []
        doc.comments.append({
            "author_id": user_id,
            "author_name": author_name,
            "text": text,
            "created_at": datetime.now().isoformat()
        })
        doc.updated_at = datetime.now()
        _add_history(doc, "COMMENT", user_id, f"Добавлен комментарий: {text[:50]}...")
        await db.commit()
        return True

async def get_document_history(doc_id: int) -> List[dict]:
    """Возвращает историю документа"""
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return []
        return doc.history or []
