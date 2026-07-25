"""靈感導師 agent（LangGraph ReAct tool-loop，見 reference/backend/langgraph-agent.md §4）。

主頁只有一個對話框，導師自主調度工具完成所有事：
檢索/翻找筆記、建立筆記、提出筆記修改提案、找相關與結合、整理知識體系、生成並保存心智圖。
工具的副作用走 services/；「動作」（建立了筆記、修改提案、存了心智圖…）收集到 actions
回給前端渲染成可操作的卡片。
"""

import json
from datetime import date
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from sqlalchemy import insert, select

from agents.idea_agent import _parse_json, organize_graph
from db.engine import engine
from db.tables import briefings
from llm import get_chat_model
from services import chat_service, embedding_service, mindmap_service, note_service, topic_service

# 上下文預算（估算字元數；中文約 1 字 ≈ 1 token）。超過 80% 自動把舊對話壓縮成摘要。
CONTEXT_CHAR_BUDGET = 16000
_COMPACT_THRESHOLD = 0.8
_KEEP_RECENT = 4  # 壓縮時保留最近幾則不動


class MentorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


_MENTOR_SYSTEM = """你是使用者的「靈感導師」——不只是助手，更是引導者。使用者把靈感記在這套筆記系統裡，你負責幫他延伸、結合、整理、回顧這些靈感，並主動給建議與提醒。

## 原則
- 一律用繁體中文，回覆用 markdown；提到某篇筆記時用 [#id] 標註（例如 [#12]）。
- 回答任何與使用者靈感有關的問題前，先用 search_notes / list_recent_notes / get_note 查筆記，根據筆記內容回答，不要憑空編造使用者的想法。
- 像導師一樣：給觀點、也給追問；適時指出「這幾則靈感可以合起來」「這則很久沒動了」之類的提醒。
- 一般知識問題可以直接回答，但若能連回使用者的靈感，就連回去。

## 工具使用
- 使用者要「記錄想法/新增筆記」→ create_note（標題精短、內容完整）。
- 使用者要「修改某篇筆記」或你們討論出更好的版本 → 一律 propose_note_update 提出提案（會出現「套用」按鈕讓使用者確認），絕不假裝已直接修改。
- 「找相關/可以跟什麼結合」→ find_related 或 search_notes 後給結合建議。
- 「整理知識體系/分類主題」→ organize_topics（會重建主題）。新筆記平時會自動歸入主題，只有使用者想「重新梳理全部」才用 organize_topics。
- 「畫心智圖/視覺化」→ 範圍是全部靈感就用 list_recent_notes / search_notes 取材；**指定某個主題**就先 list_topics 找到主題 id、再用 get_topic_notes 取該主題的全部筆記。然後自己組出心智圖 markdown（只用 #/##/###/#### 標題構成階層、節點 15 字內、可帶 [#id]），用 save_mindmap 保存，並告訴使用者可到「心智圖」頁查看。
- 工具回傳的 JSON 是給你看的，整理成自然的話再回覆使用者。"""


def _content_text(content) -> str:
    """AIMessage.content 可能是字串或 content blocks，統一取文字。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return str(content)


def _build_tools(user_id: int, actions: list[dict]):
    """以 user_id 閉包建立工具；副作用動作收進 actions 給前端渲染卡片。"""

    @tool
    def search_notes(query: str) -> str:
        """在使用者的靈感筆記庫做語意搜尋，回傳最相關的筆記（id、標題、摘要）。回答與靈感有關的問題前先用這個。"""
        try:
            vec = embedding_service.embed_text(user_id, query)
            found = embedding_service.similar_notes(user_id, vec, top_k=8, min_score=0.15)
        except Exception:  # embedding 未設定時退回關鍵字搜尋
            found = note_service.list_notes(user_id, q=query)[:8]
        return json.dumps(
            [
                {"id": n["id"], "title": n["title"], "snippet": n["content"][:200], "score": n.get("score")}
                for n in found
            ],
            ensure_ascii=False,
        )

    @tool
    def list_recent_notes(limit: int = 10) -> str:
        """列出使用者最近的靈感筆記（id、標題、摘要），用於回顧、找話題、盤點。"""
        notes = note_service.list_notes(user_id)[: max(1, min(limit, 30))]
        return json.dumps(
            [{"id": n["id"], "title": n["title"], "snippet": n["content"][:150]} for n in notes],
            ensure_ascii=False,
        )

    @tool
    def get_note(note_id: int) -> str:
        """取得某篇筆記的完整內容。"""
        note = note_service.get_note(user_id, note_id)
        if note is None:
            return "找不到這篇筆記"
        return json.dumps(
            {"id": note["id"], "title": note["title"], "content": note["content"]},
            ensure_ascii=False,
        )

    @tool
    def create_note(title: str, content: str) -> str:
        """替使用者建立一篇新的靈感筆記。title 精短、content 完整。"""
        note = note_service.create_note(
            user_id, title.strip()[:300] or content.strip()[:30], content.strip(), source="assistant"
        )
        actions.append({"type": "note_created", "note_id": note["id"], "title": note["title"]})
        return f"已建立筆記 [#{note['id']}] {note['title']}"

    @tool
    def propose_note_update(note_id: int, new_title: str, new_content: str, reason: str) -> str:
        """對某篇筆記提出修改提案（不會直接改；使用者會看到「套用」按鈕自行確認）。new_content 要是修改後的完整內容。"""
        note = note_service.get_note(user_id, note_id)
        if note is None:
            return "找不到這篇筆記"
        actions.append({
            "type": "note_update_proposal",
            "note_id": note_id,
            "old_title": note["title"],
            "new_title": new_title.strip()[:300] or note["title"],
            "new_content": new_content,
            "reason": reason,
        })
        return "已提出修改提案，使用者會看到提案卡片與「套用」按鈕；回覆時簡短說明改了什麼即可，不必重貼全文。"

    @tool
    def find_related(note_id: int) -> str:
        """用語意相似度找出與某篇筆記最相關的其他筆記，適合做結合建議。"""
        try:
            related = note_service.related_notes(user_id, note_id, top_k=5)
        except ValueError as e:
            return str(e)
        return json.dumps(
            [
                {"id": n["id"], "title": n["title"], "snippet": n["content"][:200], "score": n["score"]}
                for n in related
            ],
            ensure_ascii=False,
        )

    @tool
    def list_topics() -> str:
        """列出目前的知識體系主題（名稱、摘要、所含筆記）。"""
        topics = topic_service.list_topics(user_id)
        if not topics:
            return "目前還沒有整理過知識體系（可用 organize_topics 整理）"
        return json.dumps(
            [
                {"id": t["id"], "name": t["name"], "summary": t["summary"],
                 "notes": [{"id": n["id"], "title": n["title"]} for n in t["notes"]]}
                for t in topics
            ],
            ensure_ascii=False,
        )

    @tool
    def get_topic_notes(topic_id: int) -> str:
        """取得某個知識體系主題內的所有筆記（含內容）。畫該主題的心智圖、或深入分析單一主題時使用。"""
        topic = topic_service.get_topic_with_notes(user_id, topic_id)
        if topic is None:
            return "找不到這個主題（可先用 list_topics 查主題 id）"
        return json.dumps(
            {
                "id": topic["id"], "name": topic["name"], "summary": topic["summary"],
                "notes": [
                    {"id": n["id"], "title": n["title"], "content": n["content"][:400]}
                    for n in topic["notes"]
                ],
            },
            ensure_ascii=False,
        )

    @tool
    def organize_topics() -> str:
        """通讀所有筆記、重新聚合成知識體系主題（會覆蓋現有主題）。使用者要求整理/分類時使用。"""
        result = organize_graph.invoke({"user_id": user_id})["result"]["topics"]
        actions.append({
            "type": "topics_updated",
            "topics": [{"name": t["name"], "count": len(t["notes"])} for t in result],
        })
        return json.dumps(
            [{"name": t["name"], "summary": t["summary"], "count": len(t["notes"])} for t in result],
            ensure_ascii=False,
        )

    @tool
    def save_mindmap(title: str, markdown: str) -> str:
        """保存一張你組好的心智圖（markdown 用 #/##/### 標題構成階層）。使用者可到「心智圖」頁查看與下載。"""
        saved = mindmap_service.create_mindmap(user_id, title, markdown)
        actions.append({"type": "mindmap_saved", "id": saved["id"], "title": saved["title"]})
        return f"已保存心智圖「{saved['title']}」（id={saved['id']}），使用者可在「心智圖」頁查看。"

    return [
        search_notes, list_recent_notes, get_note, create_note, propose_note_update,
        find_related, list_topics, get_topic_notes, organize_topics, save_mindmap,
    ]


def _suggestions_for(llm, question: str, reply: str) -> list[str]:
    """回覆後另外生成 3 個可點的後續建議（失敗就略過，不影響主回覆）。"""
    try:
        resp = llm.invoke([
            SystemMessage(content="只輸出一個有效 JSON 物件，繁體中文。"),
            HumanMessage(content=(
                f"使用者剛說：{question[:300]}\n導師剛回答（節錄）：{reply[:800]}\n\n"
                "給 3 個使用者接下來最可能想接著問/做的建議，短到能當按鈕文字（18 字內），"
                '輸出 JSON：{"suggestions":["...","...","..."]}'
            )),
        ])
        items = _parse_json(_content_text(resp.content)).get("suggestions", [])
        return [str(s)[:40] for s in items][:3]
    except Exception:
        return []


def _setup(user_id: int, message: str, history: list[dict], note_id: int | None, summary: str):
    """組出一輪對話所需的 llm / graph / 初始訊息；actions 由工具閉包填入。"""
    actions: list[dict] = []
    tools = _build_tools(user_id, actions)
    llm = get_chat_model(user_id)
    llm_with_tools = llm.bind_tools(tools)

    system = _MENTOR_SYSTEM
    if summary:
        system += f"\n\n## 先前對話摘要\n（更早的對話已壓縮成以下摘要）\n{summary}"
    if note_id is not None:
        note = note_service.get_note(user_id, note_id)
        if note is None:
            raise ValueError("找不到筆記")
        system += (
            f"\n\n## 目前聚焦的筆記\n這場對話聚焦在筆記 [#{note['id']}]，"
            "延伸、結合、修改提案預設都圍繞它。\n"
            f"標題：{note['title']}\n內容：{note['content'][:3000]}"
        )

    msgs: list[AnyMessage] = [SystemMessage(content=system)]
    for m in history[-12:]:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    msgs.append(HumanMessage(content=message))

    def agent_node(state: MentorState) -> dict:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    def route(state: MentorState) -> str:
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    builder = StateGraph(MentorState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    graph = builder.compile()
    return llm, graph, msgs, actions


def run_mentor(
    user_id: int,
    message: str,
    history: list[dict],
    note_id: int | None = None,
    summary: str = "",
) -> dict:
    """跑一輪導師對話（非串流版）。history: [{role, content}]。"""
    llm, graph, msgs, actions = _setup(user_id, message, history, note_id, summary)
    result = graph.invoke({"messages": msgs}, config={"recursion_limit": 20})
    reply = _content_text(result["messages"][-1].content).strip()
    if not reply:
        reply = "（我完成了上面的操作。）"
    return {
        "reply": reply,
        "suggestions": _suggestions_for(llm, message, reply),
        "actions": actions,
    }


def stream_mentor(
    user_id: int,
    message: str,
    history: list[dict],
    note_id: int | None = None,
    summary: str = "",
):
    """串流版：先逐 token yield {"type":"token"}，最後 yield {"type":"final", reply/suggestions/actions}。"""
    llm, graph, msgs, actions = _setup(user_id, message, history, note_id, summary)
    reply_parts: list[str] = []
    for chunk, meta in graph.stream(
        {"messages": msgs}, config={"recursion_limit": 20}, stream_mode="messages"
    ):
        if meta.get("langgraph_node") != "agent":
            continue  # 只串流 agent node 的 LLM 輸出，工具訊息不外流
        text = _content_text(getattr(chunk, "content", ""))
        if text:
            reply_parts.append(text)
            yield {"type": "token", "text": text}
    reply = "".join(reply_parts).strip()
    if not reply:
        reply = "（我完成了上面的操作。）"
    yield {
        "type": "final",
        "reply": reply,
        "suggestions": _suggestions_for(llm, message, reply),
        "actions": actions,
    }


# ── 上下文壓縮（compact）與統計 ───────────────────────────


def context_info(user_id: int, thread: str) -> dict:
    """目前這個對話 thread 的上下文用量（摘要＋未壓縮訊息，字元估算）。"""
    s = chat_service.get_summary(user_id, thread)
    msgs = chat_service.history_after(user_id, thread, s["covered_until_id"], limit=200)
    used = len(s["summary"]) + sum(len(m["content"]) for m in msgs)
    return {
        "used": used,
        "budget": CONTEXT_CHAR_BUDGET,
        "percent": min(100, round(used * 100 / CONTEXT_CHAR_BUDGET)),
        "summary": s["summary"],
    }


def compact_if_needed(user_id: int, thread: str) -> None:
    """超過預算 80% 時，把較舊的訊息併入摘要（保留最近幾則），像 Claude Code 的 compact。"""
    s = chat_service.get_summary(user_id, thread)
    msgs = chat_service.history_after(user_id, thread, s["covered_until_id"], limit=200)
    used = len(s["summary"]) + sum(len(m["content"]) for m in msgs)
    if used < int(CONTEXT_CHAR_BUDGET * _COMPACT_THRESHOLD) or len(msgs) <= _KEEP_RECENT + 2:
        return
    old = msgs[:-_KEEP_RECENT]
    lines = "\n".join(
        f"{'使用者' if m['role'] == 'user' else '導師'}：{m['content'][:600]}" for m in old
    )
    try:
        llm = get_chat_model(user_id)
        resp = llm.invoke([
            SystemMessage(content="你是對話摘要器。只輸出摘要文字本身，繁體中文。"),
            HumanMessage(content=(
                f"既有摘要：\n{s['summary'] or '（無）'}\n\n新的對話段落：\n{lines}\n\n"
                "請把兩者合併成一份更新後的摘要（500 字內），務必保留："
                "使用者的目標與偏好、討論過的靈感筆記（含 [#id]）與結論、尚未完成的事項。"
            )),
        ])
        new_summary = _content_text(resp.content).strip()[:2000]
    except Exception:  # 摘要失敗就下次再試，不影響對話
        return
    if new_summary:
        chat_service.set_summary(user_id, thread, new_summary, old[-1]["id"])


# ── 每日導師簡報（每帳號每天生成一次並快取） ──────────────────

_FALLBACK_BRIEFING = {
    "greeting": "嗨，今天想到什麼靈感？隨時丟給我，我幫你記下、延伸或整理。",
    "suggestions": ["幫我回顧最近的靈感", "我最近的靈感可以怎麼延伸？", "把我的靈感整理成主題"],
}


def daily_briefing(user_id: int) -> dict:
    today = date.today().isoformat()
    with engine.connect() as conn:
        row = conn.execute(
            select(briefings.c.payload).where(
                briefings.c.user_id == user_id, briefings.c.date == today
            )
        ).first()
    if row is not None:
        return row[0]

    notes = note_service.list_notes(user_id)
    if not notes:
        return {
            "greeting": "歡迎！這裡還空空的——把腦中任何一閃而過的想法丟進來，我幫你記下並陪你把它養大。",
            "suggestions": ["我想記下一個新靈感", "這套系統可以幫我做什麼？"],
        }

    listing = "\n".join(f"[#{n['id']}] {n['title']}：{n['content'][:120]}" for n in notes[:10])
    try:
        llm = get_chat_model(user_id)
        resp = llm.invoke([
            SystemMessage(content="你是使用者的靈感導師。只輸出一個有效 JSON 物件，繁體中文。"),
            HumanMessage(content=(
                f"使用者共有 {len(notes)} 篇靈感筆記，最近的幾篇：\n{listing}\n\n"
                "請以導師口吻寫一段今日問候（2~3 句：回顧或點出值得注意的方向、給一個具體提醒或建議），"
                "並給 3 個可直接點擊的建議問題/指令（18 字內），輸出 JSON：\n"
                '{"greeting":"...","suggestions":["...","...","..."]}'
            )),
        ])
        payload = _parse_json(_content_text(resp.content))
        payload = {
            "greeting": str(payload.get("greeting", ""))[:500] or _FALLBACK_BRIEFING["greeting"],
            "suggestions": [str(s)[:40] for s in payload.get("suggestions", [])][:3],
        }
    except Exception:
        return _FALLBACK_BRIEFING  # LLM 未設定/失敗：給靜態版，不快取（之後設定好可再生成）

    with engine.begin() as conn:
        conn.execute(insert(briefings).values(user_id=user_id, date=today, payload=payload))
    return payload
