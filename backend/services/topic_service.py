"""知識體系主題：agent「整理」整批重建（replace_topics）＋新筆記自動歸類（classify_note）。"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import delete, insert, select, update

from db.engine import engine
from db.tables import note_topics, notes, topics
from llm import get_chat_model


def _loose_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(text).strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else {}


def list_topics(user_id: int) -> list[dict]:
    with engine.connect() as conn:
        topic_rows = conn.execute(
            select(topics).where(topics.c.user_id == user_id).order_by(topics.c.id)
        ).fetchall()
        result = []
        for t in topic_rows:
            td = dict(t._mapping)
            note_rows = conn.execute(
                select(notes.c.id, notes.c.title)
                .join(note_topics, note_topics.c.note_id == notes.c.id)
                .where(note_topics.c.topic_id == td["id"])
            )
            td["notes"] = [dict(r._mapping) for r in note_rows]
            result.append(td)
    return result


def get_topic_with_notes(user_id: int, topic_id: int) -> dict | None:
    """含筆記全文，給心智圖 agent 用。"""
    with engine.connect() as conn:
        row = conn.execute(
            select(topics).where(topics.c.id == topic_id, topics.c.user_id == user_id)
        ).first()
        if row is None:
            return None
        td = dict(row._mapping)
        note_rows = conn.execute(
            select(notes.c.id, notes.c.title, notes.c.content)
            .join(note_topics, note_topics.c.note_id == notes.c.id)
            .where(note_topics.c.topic_id == topic_id)
        )
        td["notes"] = [dict(r._mapping) for r in note_rows]
    return td


def classify_note(user_id: int, note_id: int) -> None:
    """新筆記自動融入知識體系：歸入既有主題、必要時開新主題或微調主題名（讓體系保持流動）。
    在背景執行緒呼叫，失敗靜默略過，不影響筆記本身。"""
    existing = list_topics(user_id)
    if not existing:
        return  # 還沒建立過知識體系：等使用者請導師整理一次
    with engine.connect() as conn:
        row = conn.execute(
            select(notes.c.title, notes.c.content).where(
                notes.c.id == note_id, notes.c.user_id == user_id
            )
        ).first()
    if row is None:
        return
    title, content = row

    topic_desc = "\n".join(
        f"[{t['id']}] {t['name']}：{t['summary']}（{len(t['notes'])} 篇）" for t in existing
    )
    llm = get_chat_model(user_id)
    resp = llm.invoke([
        SystemMessage(content="你負責維護使用者的知識體系。只輸出一個有效 JSON 物件，繁體中文。"),
        HumanMessage(content=(
            f"既有主題：\n{topic_desc}\n\n新的靈感筆記：\n標題：{title}\n內容：{content[:800]}\n\n"
            "請把新筆記融入知識體系，輸出 JSON：\n"
            '{"topic_ids":[適合歸入的既有主題id，可多個或空],'
            '"new_topic":{"name":"...","summary":"..."} 或 null（只有真的都不適合才開新主題）,'
            '"rename":{"id":既有主題id,"name":"更貼切的新名稱"} 或 null（僅當納入這筆後名稱明顯該調整）}'
        )),
    ])
    data = _loose_json(resp.content)

    valid_ids = {t["id"] for t in existing}
    with engine.begin() as conn:
        for tid in data.get("topic_ids") or []:
            if isinstance(tid, int) and tid in valid_ids:
                dup = conn.execute(
                    select(note_topics.c.note_id).where(
                        note_topics.c.topic_id == tid, note_topics.c.note_id == note_id
                    )
                ).first()
                if dup is None:
                    conn.execute(insert(note_topics).values(topic_id=tid, note_id=note_id))
        new_topic = data.get("new_topic")
        if isinstance(new_topic, dict) and str(new_topic.get("name", "")).strip():
            new_tid = conn.execute(
                insert(topics).values(
                    user_id=user_id,
                    name=str(new_topic["name"]).strip()[:200],
                    summary=str(new_topic.get("summary", "")),
                )
            ).inserted_primary_key[0]
            conn.execute(insert(note_topics).values(topic_id=new_tid, note_id=note_id))
        rename = data.get("rename")
        if (
            isinstance(rename, dict)
            and isinstance(rename.get("id"), int)
            and rename["id"] in valid_ids
            and str(rename.get("name", "")).strip()
        ):
            conn.execute(
                update(topics)
                .where(topics.c.id == rename["id"], topics.c.user_id == user_id)
                .values(name=str(rename["name"]).strip()[:200])
            )


def replace_topics(user_id: int, topic_defs: list[dict]) -> list[dict]:
    """用 agent 整理結果整批重建該使用者的主題。topic_defs: [{name, summary, note_ids}]"""
    with engine.begin() as conn:
        old_ids = [r[0] for r in conn.execute(select(topics.c.id).where(topics.c.user_id == user_id))]
        if old_ids:
            conn.execute(delete(note_topics).where(note_topics.c.topic_id.in_(old_ids)))
            conn.execute(delete(topics).where(topics.c.user_id == user_id))
        valid_note_ids = {
            r[0] for r in conn.execute(select(notes.c.id).where(notes.c.user_id == user_id))
        }
        for t in topic_defs:
            name = str(t.get("name", "")).strip()[:200]
            if not name:
                continue
            tid = conn.execute(
                insert(topics).values(user_id=user_id, name=name, summary=str(t.get("summary", "")))
            ).inserted_primary_key[0]
            for nid in dict.fromkeys(t.get("note_ids", [])):
                if isinstance(nid, int) and nid in valid_note_ids:
                    conn.execute(insert(note_topics).values(topic_id=tid, note_id=nid))
    return list_topics(user_id)
