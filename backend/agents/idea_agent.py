"""靈感 agent（LangGraph，寫法見 reference/backend/langgraph-agent.md）。

五個 graph，router 直接 invoke，結果都放 state["result"]：
- extend_graph   靈感延伸與引導（load_note → extend）
- connect_graph  靈感連結與結合（load_note → find_related → 條件分支 → combine / empty）
- qa_graph       知識體系問答 RAG（retrieve → answer，回答可萃取新靈感）
- mindmap_graph  心智圖 markdown（gather → mindmap）
- organize_graph 知識體系整理（gather → cluster → save）
"""

import json
import re
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from llm import get_chat_model
from services import embedding_service, note_service, topic_service


class IdeaState(TypedDict, total=False):
    user_id: int
    note_id: int
    question: str
    topic_id: int | None
    note: dict
    related: list[dict]
    context: list[dict]
    result: dict


_SYSTEM = (
    "你是使用者的靈感夥伴與第二大腦。所有輸出用繁體中文。"
    "回覆必須是單一個有效 JSON 物件，不要加任何 JSON 以外的文字或說明。"
)


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"模型回應不是有效 JSON：{text[:200]}")


def _ask_json(user_id: int, prompt: str) -> dict:
    llm = get_chat_model(user_id)
    resp = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    return _parse_json(resp.content)


def _load_note(state: IdeaState) -> dict:
    note = note_service.get_note(state["user_id"], state["note_id"])
    if note is None:
        raise ValueError("找不到筆記")
    return {"note": note}


# ── 1. 靈感延伸與引導 ─────────────────────────────────────


def _extend(state: IdeaState) -> dict:
    note = state["note"]
    data = _ask_json(
        state["user_id"],
        f"這是我的一篇靈感筆記：\n標題:{note['title']}\n內容:{note['content'][:3000]}\n\n"
        "請幫我延伸這個靈感，輸出 JSON：\n"
        '{"extensions":[{"title":"延伸方向的短標題","idea":"具體延伸想法，2~4 句"}],'
        '"questions":["引導我更深入思考的問題"],"next_steps":["具體可執行的下一步"]}\n'
        "extensions 給 3~5 個、questions 與 next_steps 各 3 個。"
    )
    return {"result": {
        "extensions": data.get("extensions", []),
        "questions": data.get("questions", []),
        "next_steps": data.get("next_steps", []),
    }}


_b = StateGraph(IdeaState)
_b.add_node("load_note", _load_note)
_b.add_node("extend", _extend)
_b.add_edge(START, "load_note")
_b.add_edge("load_note", "extend")
_b.add_edge("extend", END)
extend_graph = _b.compile()


# ── 2. 靈感連結與結合 ─────────────────────────────────────


def _find_related(state: IdeaState) -> dict:
    related = note_service.related_notes(state["user_id"], state["note_id"], top_k=5)
    return {"related": related}


def _route_related(state: IdeaState) -> str:
    return "combine" if state.get("related") else "empty"


def _combine(state: IdeaState) -> dict:
    note = state["note"]
    related = state["related"]
    listing = "\n\n".join(
        f"[#{n['id']}] {n['title']}（相似度 {n['score']}）\n{n['content'][:400]}" for n in related
    )
    data = _ask_json(
        state["user_id"],
        f"當前靈感筆記：\n標題:{note['title']}\n內容:{note['content'][:2000]}\n\n"
        f"以下是與它語意相關的其他靈感筆記：\n{listing}\n\n"
        "請思考當前靈感能與哪些筆記結合、結合後可以發展成什麼，輸出 JSON：\n"
        '{"summary":"整體觀察，1~2 句",'
        '"combinations":[{"note_id":相關筆記的數字id,"idea":"結合後可發展成什麼，2~4 句"}]}'
    )
    by_id = {n["id"]: n for n in related}
    combos = []
    for c in data.get("combinations", []):
        ref = by_id.get(c.get("note_id"))
        if ref is None:
            continue
        combos.append({
            "note_id": ref["id"], "note_title": ref["title"],
            "score": ref["score"], "idea": c.get("idea", ""),
        })
    return {"result": {
        "summary": data.get("summary", ""),
        "combinations": combos,
        "related": [{"id": n["id"], "title": n["title"], "score": n["score"]} for n in related],
    }}


def _empty_related(state: IdeaState) -> dict:
    return {"result": {
        "summary": "目前找不到夠相關的其他靈感（可能筆記還太少，或多數筆記尚未向量化）。",
        "combinations": [],
        "related": [],
    }}


_b = StateGraph(IdeaState)
_b.add_node("load_note", _load_note)
_b.add_node("find_related", _find_related)
_b.add_node("combine", _combine)
_b.add_node("empty", _empty_related)
_b.add_edge(START, "load_note")
_b.add_edge("load_note", "find_related")
_b.add_conditional_edges("find_related", _route_related, {"combine": "combine", "empty": "empty"})
_b.add_edge("combine", END)
_b.add_edge("empty", END)
connect_graph = _b.compile()


# ── 3. 知識體系問答（RAG，可萃取新靈感）──────────────────────


def _retrieve(state: IdeaState) -> dict:
    vec = embedding_service.embed_text(state["user_id"], state["question"])
    context = embedding_service.similar_notes(state["user_id"], vec, top_k=8, min_score=0.15)
    return {"context": context}


def _answer(state: IdeaState) -> dict:
    context = state.get("context", [])
    if context:
        sources = "\n\n".join(
            f"[#{n['id']}] {n['title']}\n{n['content'][:600]}" for n in context
        )
        source_hint = f"以下是使用者的靈感筆記（引用時用 [#id] 標註來源）：\n{sources}"
    else:
        source_hint = "（找不到相關筆記，請誠實說明，並就問題本身給出啟發性的思考。）"
    data = _ask_json(
        state["user_id"],
        f"{source_hint}\n\n使用者的問題：{state['question']}\n\n"
        "請根據筆記回答問題，並從這次問答中萃取值得記下的新靈感（沒有就給空陣列），輸出 JSON：\n"
        '{"answer":"markdown 格式的回答，引用筆記用 [#id]",'
        '"sparks":[{"title":"新靈感標題","content":"新靈感內容，2~4 句"}]}'
    )
    return {"result": {
        "answer": data.get("answer", ""),
        "sparks": data.get("sparks", []),
        "sources": [{"id": n["id"], "title": n["title"], "score": n["score"]} for n in context],
    }}


_b = StateGraph(IdeaState)
_b.add_node("retrieve", _retrieve)
_b.add_node("answer", _answer)
_b.add_edge(START, "retrieve")
_b.add_edge("retrieve", "answer")
_b.add_edge("answer", END)
qa_graph = _b.compile()


# ── 4. 心智圖 ───────────────────────────────────────────


def _gather_scope(state: IdeaState) -> dict:
    """取材範圍：topic_id → 該主題筆記；question（自訂範圍描述）→ 語意檢索；否則全部。"""
    user_id = state["user_id"]
    topic_id = state.get("topic_id")
    query = (state.get("question") or "").strip()
    if topic_id:
        topic = topic_service.get_topic_with_notes(user_id, topic_id)
        if topic is None:
            raise ValueError("找不到主題")
        return {"context": topic["notes"][:80], "note": {"title": topic["name"]}}
    if query:
        try:
            vec = embedding_service.embed_text(user_id, query)
            found = embedding_service.similar_notes(user_id, vec, top_k=40, min_score=0.12)
        except Exception:  # embedding 未設定時退回關鍵字搜尋
            found = note_service.list_notes(user_id, q=query)[:40]
        if not found:
            raise ValueError(f"找不到與「{query}」相關的靈感筆記")
        return {"context": found[:60], "note": {"title": query}}
    all_notes = note_service.list_notes(user_id)
    return {"context": all_notes[:80], "note": {"title": "我的靈感"}}


def _mindmap(state: IdeaState) -> dict:
    notes_list = state.get("context", [])
    if not notes_list:
        raise ValueError("還沒有任何筆記，先去記幾個靈感吧")
    listing = "\n\n".join(
        f"[#{n['id']}] {n['title']}\n{n['content'][:300]}" for n in notes_list
    )
    data = _ask_json(
        state["user_id"],
        f"主題：{state['note']['title']}\n以下是靈感筆記：\n{listing}\n\n"
        "請把這些靈感整理成心智圖，輸出 JSON：\n"
        '{"markdown":"# 中心主題\\n## 分支\\n### 子節點..."}\n'
        "規則：只用 #/##/###/#### 標題構成階層；節點文字精短（15 字內）；"
        "可在節點後用 [#id] 標註對應筆記；分支 3~7 個，涵蓋所有重要靈感。"
    )
    markdown = data.get("markdown", "").strip()
    if not markdown.startswith("#"):
        markdown = f"# {state['note']['title']}\n{markdown}"
    return {"result": {
        "markdown": markdown,
        "note_count": len(notes_list),
        "title": state["note"]["title"],
    }}


_b = StateGraph(IdeaState)
_b.add_node("gather", _gather_scope)
_b.add_node("mindmap", _mindmap)
_b.add_edge(START, "gather")
_b.add_edge("gather", "mindmap")
_b.add_edge("mindmap", END)
mindmap_graph = _b.compile()


# ── 5. 知識體系整理（聚類成主題）────────────────────────────


def _gather_all(state: IdeaState) -> dict:
    all_notes = note_service.list_notes(state["user_id"])
    if not all_notes:
        raise ValueError("還沒有任何筆記，先去記幾個靈感吧")
    return {"context": all_notes[:150]}


def _cluster(state: IdeaState) -> dict:
    listing = "\n".join(
        f"[#{n['id']}] {n['title']}：{n['content'][:200]}" for n in state["context"]
    )
    data = _ask_json(
        state["user_id"],
        f"以下是使用者的全部靈感筆記：\n{listing}\n\n"
        "請把這些靈感聚合成知識體系的主題，輸出 JSON：\n"
        '{"topics":[{"name":"主題名","summary":"這個主題在講什麼，1~2 句","note_ids":[數字id]}]}\n'
        "規則：主題 3~8 個（筆記很少就少一點）；每篇筆記至少歸入一個主題，可跨主題。"
    )
    return {"result": {"topics": data.get("topics", [])}}


def _save_topics(state: IdeaState) -> dict:
    saved = topic_service.replace_topics(state["user_id"], state["result"]["topics"])
    return {"result": {"topics": saved}}


_b = StateGraph(IdeaState)
_b.add_node("gather", _gather_all)
_b.add_node("cluster", _cluster)
_b.add_node("save", _save_topics)
_b.add_edge(START, "gather")
_b.add_edge("gather", "cluster")
_b.add_edge("cluster", "save")
_b.add_edge("save", END)
organize_graph = _b.compile()
