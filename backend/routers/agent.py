"""AI agent 端點：invoke LangGraph graph，結果取 state["result"]。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.idea_agent import (
    connect_graph,
    extend_graph,
    mindmap_graph,
    organize_graph,
    qa_graph,
)
from routers.deps import get_current_user
from services import mindmap_service

router = APIRouter(prefix="/agent", tags=["agent"])


class NoteRefIn(BaseModel):
    note_id: int


class QAIn(BaseModel):
    question: str


class MindmapIn(BaseModel):
    topic_id: int | None = None
    query: str | None = None  # 自訂範圍描述（有值時以語意檢索取材）


def _run(graph, payload: dict) -> dict:
    try:
        return graph.invoke(payload)["result"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 - LLM/網路錯誤統一回 502 讓前端顯示
        raise HTTPException(status_code=502, detail=f"AI 執行失敗：{e}")


@router.post("/extend")
def extend(body: NoteRefIn, user: dict = Depends(get_current_user)):
    return _run(extend_graph, {"user_id": user["id"], "note_id": body.note_id})


@router.post("/connect")
def connect(body: NoteRefIn, user: dict = Depends(get_current_user)):
    return _run(connect_graph, {"user_id": user["id"], "note_id": body.note_id})


@router.post("/qa")
def qa(body: QAIn, user: dict = Depends(get_current_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="問題不可為空")
    return _run(qa_graph, {"user_id": user["id"], "question": question})


@router.post("/mindmap")
def mindmap(body: MindmapIn, user: dict = Depends(get_current_user)):
    result = _run(
        mindmap_graph,
        {"user_id": user["id"], "topic_id": body.topic_id, "question": body.query or ""},
    )
    saved = mindmap_service.create_mindmap(
        user["id"], result["title"], result["markdown"],
        topic_id=body.topic_id, query=body.query,
    )
    return {**result, "id": saved["id"]}


@router.post("/organize")
def organize(user: dict = Depends(get_current_user)):
    return _run(organize_graph, {"user_id": user["id"]})
