# AI Agent 開發慣例（LangGraph · 可攜式）

> 開發 AI agent 時的統一寫法。**核心：用 `from langgraph.graph import StateGraph, START, END` 這種寫法的 LangGraph 版本**（新版 graph API，非舊的 `MessageGraph` / 舊 entrypoint 寫法）。
> LLM 的建構統一走 `llm-integration.md`（ChatOllama / ChatOpenAI），本文件只談 graph 結構。

---

## 0. 一句話總結

用 **LangGraph 的 `StateGraph`** 建圖：定義一個 `State`（`TypedDict`）→ 加 node（純函式，收 state 回 partial state）→ 用 `START` / `END` 與條件邊接線 → `compile()` 成 app → `invoke` / `stream` 執行。

---

## 1. 版本與 import（務必用這種寫法）

```python
from langgraph.graph import StateGraph, START, END
```

- 一定用 **`START` / `END` 常數 + `add_edge`** 接進出點，**不要**用舊版 `set_entry_point()` / `set_finish_point()`。
- `requirements.txt`：`langgraph>=0.2`、`langchain-core>=0.3`（LLM 另見 `llm-integration.md`）。

---

## 2. 最小骨架

```python
# backend/agents/basic_agent.py
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# 1) State：整張圖共享的狀態（node 回傳 partial 會 merge 進來）
class State(TypedDict):
    question: str
    answer: str


# 2) Node：純函式，(state) -> partial state
def answer_node(state: State) -> dict:
    q = state["question"]
    return {"answer": f"你問了：{q}"}


# 3) 建圖：加 node、用 START/END 接線
builder = StateGraph(State)
builder.add_node("answer", answer_node)
builder.add_edge(START, "answer")
builder.add_edge("answer", END)

# 4) 編譯成可執行 app
graph = builder.compile()


if __name__ == "__main__":
    result = graph.invoke({"question": "今天天氣如何？"})
    print(result["answer"])
```

---

## 3. 累加型 State（訊息 / 清單用 reducer）

需要「多個 node 往同一欄位累加」時（如對話訊息），用 `Annotated` + reducer，**不要**每次覆寫：

```python
from typing import Annotated, TypedDict
from operator import add

from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # 訊息累加
    scratch: Annotated[list[str], add]                   # 一般清單累加
```

---

## 4. 條件分支（`add_conditional_edges`）

用一個「router 函式」回傳下一個 node 名稱（或 `END`）決定走向：

```python
def route(state: State) -> str:
    if state.get("need_tool"):
        return "call_tool"
    return "respond"

builder.add_conditional_edges(
    "think",                                  # 從哪個 node 出發
    route,                                    # 回傳下一步 key 的函式
    {"call_tool": "call_tool", "respond": "respond"},  # key → node 對照
)
```

**ReAct / tool 迴圈** 的典型結構：`agent`（LLM 決策）→ 條件邊 → 有 tool call 就去 `tools` 再回 `agent`，否則到 `END`。

---

## 5. 接 LLM node（配合 llm-integration.md）

LLM 一律從 `llm/` 建構好再注入，node 內只呼叫，**不在 node 裡硬編 model 名稱 / base_url**：

```python
from llm import get_chat_model   # 見 llm-integration.md

def llm_node(state: State) -> dict:
    llm = get_chat_model()                    # ChatOllama 或 ChatOpenAI
    resp = llm.invoke(state["messages"])
    return {"messages": [resp]}
```

需要工具時用 `llm.bind_tools([...])`，並搭配 `langgraph.prebuilt.ToolNode` 執行工具。

---

## 6. 串流與持久化

- **串流**：`for chunk in graph.stream(input, stream_mode="values"): ...`；接到 FastAPI 就包成 SSE / `StreamingResponse`（讓前端逐步顯示，見前端「多秒操作進度」慣例）。
- **記憶 / 續跑**：需要跨呼叫記憶時 `compile(checkpointer=...)`（如 `MemorySaver`，或正式環境用 DB checkpointer），呼叫時帶 `config={"configurable": {"thread_id": "..."}}`。

---

## 7. 掛進 FastAPI

agent 編譯好的 `graph` 當單例，在 API 路由呼叫（同步 `invoke` 或串流 `stream`）：

```python
# backend/routers/chat.py
from fastapi import APIRouter
from pydantic import BaseModel

from agents.basic_agent import graph

router = APIRouter()


class ChatIn(BaseModel):
    question: str


@router.post("/chat")
def chat(body: ChatIn):
    result = graph.invoke({"question": body.question})
    return {"answer": result["answer"]}
```

---

## 8. 慣例小結

- **import 一律** `from langgraph.graph import StateGraph, START, END`。
- State 用 `TypedDict`；累加欄位用 `Annotated[..., reducer]`（訊息用 `add_messages`）。
- node 是純函式 `(state) -> dict(partial)`，副作用（DB / 外部 API）走 `services/`。
- 進出點用 `START` / `END` + `add_edge`；分支用 `add_conditional_edges`。
- LLM 建構外包給 `llm/`（`llm-integration.md`），node 不寫死模型設定。
- agent 檔案放 `backend/agents/`，編譯出的 `graph` 給 router 用。
