from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.idea_agent import mindmap_graph
from routers.deps import get_current_user
from services import mindmap_service, topic_service

router = APIRouter(prefix="/mindmaps", tags=["mindmaps"])


class MindmapUpdateIn(BaseModel):
    title: str
    markdown: str


@router.get("")
def list_mindmaps(user: dict = Depends(get_current_user)):
    return mindmap_service.list_mindmaps(user["id"])


@router.put("/{mindmap_id}")
def update_mindmap(mindmap_id: int, body: MindmapUpdateIn, user: dict = Depends(get_current_user)):
    if mindmap_service.get_mindmap(user["id"], mindmap_id) is None:
        raise HTTPException(status_code=404, detail="找不到心智圖")
    title = body.title.strip() or "未命名心智圖"
    mindmap_service.update_mindmap(user["id"], mindmap_id, title, body.markdown)
    return mindmap_service.get_mindmap(user["id"], mindmap_id)


@router.post("/{mindmap_id}/regenerate")
def regenerate_mindmap(mindmap_id: int, user: dict = Depends(get_current_user)):
    """用當初的範圍（主題/自訂描述/全部）重新取材、重畫，覆蓋原本的 markdown。"""
    m = mindmap_service.get_mindmap(user["id"], mindmap_id)
    if m is None:
        raise HTTPException(status_code=404, detail="找不到心智圖")

    payload = {"user_id": user["id"], "topic_id": None, "question": ""}
    if m.get("topic_id") and topic_service.get_topic_with_notes(user["id"], m["topic_id"]):
        payload["topic_id"] = m["topic_id"]
    elif m.get("query"):
        payload["question"] = m["query"]
    elif m["title"] and m["title"] != "我的靈感":
        # 舊資料（或導師存的）沒記範圍：用標題當檢索描述
        payload["question"] = m["title"]

    try:
        result = mindmap_graph.invoke(payload)["result"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI 執行失敗：{e}")

    mindmap_service.update_mindmap(user["id"], mindmap_id, m["title"], result["markdown"])
    updated = mindmap_service.get_mindmap(user["id"], mindmap_id)
    return {**updated, "note_count": result["note_count"]}


@router.delete("/{mindmap_id}")
def delete_mindmap(mindmap_id: int, user: dict = Depends(get_current_user)):
    mindmap_service.delete_mindmap(user["id"], mindmap_id)
    return {"ok": True}
