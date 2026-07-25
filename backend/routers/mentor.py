"""靈感導師端點：主頁與筆記聚焦對話共用（thread 區分）；含上下文壓縮與統計。"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.mentor_agent import (
    compact_if_needed,
    context_info,
    daily_briefing,
    run_mentor,
    stream_mentor,
)
from routers.deps import get_current_user
from services import chat_service

router = APIRouter(prefix="/agent/mentor", tags=["mentor"])


class MentorIn(BaseModel):
    message: str
    note_id: int | None = None


def _thread(note_id: int | None) -> str:
    return f"note:{note_id}" if note_id else "main"


@router.post("")
def chat(body: MentorIn, user: dict = Depends(get_current_user)):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="訊息不可為空")
    thread = _thread(body.note_id)
    summary_row = chat_service.get_summary(user["id"], thread)
    history = chat_service.history_after(
        user["id"], thread, summary_row["covered_until_id"], limit=30
    )
    try:
        result = run_mentor(
            user["id"], message, history,
            note_id=body.note_id, summary=summary_row["summary"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 - LLM/網路錯誤統一回 502 讓前端顯示
        raise HTTPException(status_code=502, detail=f"導師執行失敗：{e}")
    chat_service.append(user["id"], thread, "user", message)
    chat_service.append(
        user["id"], thread, "assistant", result["reply"],
        {"suggestions": result["suggestions"], "actions": result["actions"]},
    )
    compact_if_needed(user["id"], thread)  # 超過門檻自動把舊對話壓成摘要
    result["context"] = context_info(user["id"], thread)
    return result


@router.post("/stream")
def chat_stream(body: MentorIn, user: dict = Depends(get_current_user)):
    """SSE 串流版：token 事件逐字輸出，done 事件帶完整結果（前端主要走這支）。"""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="訊息不可為空")
    thread = _thread(body.note_id)
    summary_row = chat_service.get_summary(user["id"], thread)
    history = chat_service.history_after(
        user["id"], thread, summary_row["covered_until_id"], limit=30
    )

    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def gen():
        try:
            for ev in stream_mentor(
                user["id"], message, history,
                note_id=body.note_id, summary=summary_row["summary"],
            ):
                if ev["type"] == "final":
                    chat_service.append(user["id"], thread, "user", message)
                    chat_service.append(
                        user["id"], thread, "assistant", ev["reply"],
                        {"suggestions": ev["suggestions"], "actions": ev["actions"]},
                    )
                    compact_if_needed(user["id"], thread)
                    yield _sse({
                        "type": "done",
                        "reply": ev["reply"],
                        "suggestions": ev["suggestions"],
                        "actions": ev["actions"],
                        "context": context_info(user["id"], thread),
                    })
                else:
                    yield _sse(ev)
        except ValueError as e:
            yield _sse({"type": "error", "message": str(e)})
        except Exception as e:  # noqa: BLE001 - 串流中的錯誤以事件回報
            yield _sse({"type": "error", "message": f"導師執行失敗：{e}"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history")
def get_history(note_id: int | None = None, user: dict = Depends(get_current_user)):
    return chat_service.history(user["id"], _thread(note_id), limit=100)


@router.delete("/history")
def clear_history(note_id: int | None = None, user: dict = Depends(get_current_user)):
    chat_service.clear(user["id"], _thread(note_id))
    return {"ok": True}


@router.get("/context")
def get_context(note_id: int | None = None, user: dict = Depends(get_current_user)):
    return context_info(user["id"], _thread(note_id))


@router.get("/briefing")
def briefing(user: dict = Depends(get_current_user)):
    return daily_briefing(user["id"])
