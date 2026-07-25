# 資料庫慣例（SQLAlchemy Core · SQLite → PostgreSQL · 可攜式）

> 資料庫的統一寫法。**主力是 PostgreSQL，但初期先用 SQLite** 快速起步。
> **關鍵：一律用 SQLAlchemy Core 的寫法**（`Table` / `MetaData` / `select` / `insert`），不綁 ORM、不寫原生字串 SQL，這樣**只改連線字串就能從 SQLite 無縫換到 PostgreSQL**。

---

## 0. 一句話總結

用 **SQLAlchemy Core**：`MetaData` + `Table` 定義結構、`create_engine(DATABASE_URL)` 建連線、用 `select()/insert()/update()/delete()` 表達式操作。連線字串放 `.env`，**SQLite 與 PostgreSQL 之間只換 `DATABASE_URL`**。

---

## 1. 依賴

```txt
sqlalchemy>=2.0
psycopg[binary]>=3.1     # PostgreSQL 驅動（換 pg 時需要；SQLite 不用裝）
```

> SQLite 用 Python 內建驅動，不必額外裝。上 PostgreSQL 才需 `psycopg`。

---

## 2. 連線字串（只改這一行就換 DB）

放 `config.py` / `.env`（承 `backend-conventions.md` §5）：

```dotenv
# 初期：SQLite（檔案放 data/，容器掛 volume）
DATABASE_URL=sqlite:///./data/app.db

# 之後：PostgreSQL（只換這行，程式不動）
# DATABASE_URL=postgresql+psycopg://user:pass@db-host:5432/appdb
```

---

## 3. Engine（`db/engine.py`）

```python
# backend/db/engine.py
from sqlalchemy import create_engine

from config import settings

# SQLite 需要 check_same_thread=False 才能在多執行緒（FastAPI）用同一連線
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,      # 連線失效自動重連（PostgreSQL 尤其需要）
    future=True,
)
```

> 唯一的 DB 差異處理集中在這裡（SQLite 的 `check_same_thread`）。其餘程式碼對 SQLite / PostgreSQL 完全一致。

---

## 4. 表結構（Core `Table` / `MetaData`，`db/tables.py`）

**用 Core 的 `Table` 宣告，不用 ORM `declarative_base`。** 型別用可攜的通用型別（`Integer` / `String` / `Text` / `Boolean` / `DateTime` / `JSON`），避免 DB 專屬型別。

```python
# backend/db/tables.py
from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, Text, Boolean, DateTime, func,
)

metadata = MetaData()

items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(200), nullable=False),
    Column("description", Text, nullable=True),
    Column("done", Boolean, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
```

建表（開發期可用；正式環境建議用 Alembic 遷移，見 §7）：

```python
# 在 FastAPI lifespan 啟動時呼叫（backend-conventions.md §3）
from db.engine import engine
from db.tables import metadata

metadata.create_all(engine)   # 已存在的表不會重建
```

---

## 5. 查詢 / 寫入（Core 表達式，禁止字串拼 SQL）

一律用 `select() / insert() / update() / delete()` 表達式，參數化由 SQLAlchemy 處理（防注入、跨 DB 一致）：

```python
# backend/services/item_service.py
from sqlalchemy import select, insert, update, delete

from db.engine import engine
from db.tables import items


def list_items() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(select(items).order_by(items.c.created_at.desc()))
        return [dict(r._mapping) for r in rows]


def create_item(name: str, description: str | None = None) -> int:
    with engine.begin() as conn:                 # begin() 自動 commit
        result = conn.execute(
            insert(items).values(name=name, description=description)
        )
        return result.inserted_primary_key[0]


def mark_done(item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(update(items).where(items.c.id == item_id).values(done=True))


def remove_item(item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(items).where(items.c.id == item_id))
```

- 讀用 `engine.connect()`；寫用 `engine.begin()`（進出自動 commit / rollback）。
- 結果列轉 dict：`dict(row._mapping)`。
- **絕不字串拼 SQL**；所有條件用 `items.c.xxx == ...` 表達式，換 DB 不必改。

---

## 6. SQLite → PostgreSQL 遷移檢查表

從 SQLite 換到 PostgreSQL 時，理論上只改 `DATABASE_URL`。仍要留意：

- **驅動**：安裝 `psycopg[binary]`，URL 用 `postgresql+psycopg://`。
- **型別可攜**：用通用型別（見 §4）；別用 SQLite 專屬技巧。需要自增大 key 時 `Integer primary_key autoincrement`（Core 會對應 PG 的 identity/serial）。
- **布林 / 時間**：用 `Boolean` / `DateTime(timezone=True)`，別存 0/1 字串或本地時間字串。
- **JSON**：用 SQLAlchemy 的 `JSON` 型別（SQLite 存文字、PG 存 jsonb，程式一致）。
- **併發**：PostgreSQL 才真正支援多連線寫入；SQLite 高併發會鎖。`pool_pre_ping=True` 已設。
- **大小寫 / identifier**：表名欄名一律小寫、蛇底線，避免 PG 需引號。

---

## 7. 遷移管理（正式環境）

開發期用 `metadata.create_all()` 夠用；**正式 / 需要改欄位時用 Alembic**：

```txt
alembic>=1.13
```

- `alembic init`，`env.py` 讀同一個 `settings.database_url` 與 `metadata`（`target_metadata = metadata`）。
- 改 `tables.py` 後 `alembic revision --autogenerate -m "..."` → `alembic upgrade head`。
- 同一套 migration 對 SQLite / PostgreSQL 皆可跑（因為都走 Core metadata）。

---

## 8. 慣例小結

- **SQLAlchemy Core**（`Table` / `MetaData` / `select` 表達式），**不用 ORM、不拼字串 SQL**。
- 連線集中在 `db/engine.py`；表結構在 `db/tables.py`；操作在 `services/`。
- **換 DB 只改 `DATABASE_URL`**：SQLite（`sqlite:///./data/app.db`）→ PostgreSQL（`postgresql+psycopg://...`）。
- 型別選可攜通用型別；SQLite 檔放 `data/`（容器掛 volume）。
- 正式環境用 Alembic 管遷移，讀同一個 `metadata`。
