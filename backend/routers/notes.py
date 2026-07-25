from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_current_user
from services import note_service

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str = ""
    content: str = ""
    source: str = "manual"
    # 由 AI 結果「存成新靈感」時，順便和來源筆記建立連結
    link_from_note_id: int | None = None
    link_reason: str = ""


class NoteUpdateIn(BaseModel):
    title: str
    content: str


class LinkIn(BaseModel):
    to_note_id: int
    reason: str = ""


def _derive_title(content: str) -> str:
    first_line = content.strip().splitlines()[0] if content.strip() else ""
    return first_line[:30]


@router.get("")
def list_notes(q: str | None = None, user: dict = Depends(get_current_user)):
    return note_service.list_notes(user["id"], q)


@router.post("")
def create_note(body: NoteIn, user: dict = Depends(get_current_user)):
    content = body.content.strip()
    title = body.title.strip() or _derive_title(content)
    if not title:
        raise HTTPException(status_code=400, detail="內容不可為空")
    note = note_service.create_note(user["id"], title, content, body.source)
    if body.link_from_note_id:
        try:
            note_service.create_link(
                user["id"], body.link_from_note_id, note["id"], body.link_reason
            )
        except ValueError:
            pass  # 連結失敗不影響筆記建立
    return note


# 注意：/links/{link_id} 要宣告在 /{note_id} 之前，避免被當成 note_id 匹配
@router.delete("/links/{link_id}")
def delete_link(link_id: int, user: dict = Depends(get_current_user)):
    note_service.delete_link(user["id"], link_id)
    return {"ok": True}


@router.get("/{note_id}")
def get_note(note_id: int, user: dict = Depends(get_current_user)):
    note = note_service.get_note(user["id"], note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="找不到筆記")
    return note


@router.put("/{note_id}")
def update_note(note_id: int, body: NoteUpdateIn, user: dict = Depends(get_current_user)):
    title = body.title.strip() or _derive_title(body.content)
    if not title:
        raise HTTPException(status_code=400, detail="內容不可為空")
    note = note_service.update_note(user["id"], note_id, title, body.content.strip())
    if note is None:
        raise HTTPException(status_code=404, detail="找不到筆記")
    return note


@router.delete("/{note_id}")
def delete_note(note_id: int, user: dict = Depends(get_current_user)):
    note_service.delete_note(user["id"], note_id)
    return {"ok": True}


@router.get("/{note_id}/related")
def related_notes(note_id: int, user: dict = Depends(get_current_user)):
    try:
        return note_service.related_notes(user["id"], note_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{note_id}/links")
def list_links(note_id: int, user: dict = Depends(get_current_user)):
    return note_service.list_links(user["id"], note_id)


@router.post("/{note_id}/links")
def create_link(note_id: int, body: LinkIn, user: dict = Depends(get_current_user)):
    try:
        note_service.create_link(user["id"], note_id, body.to_note_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
