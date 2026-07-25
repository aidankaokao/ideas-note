from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(100), nullable=False, unique=True),
    Column("password_hash", String(200), nullable=False),
    Column("is_admin", Boolean, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("title", String(300), nullable=False),
    Column("content", Text, nullable=False, server_default=""),
    # 來源：manual（手動）/ agent-extend（AI 延伸存回）/ qa-extract（問答萃取）
    Column("source", String(30), nullable=False, server_default="manual"),
    Column("embedding", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), server_default=func.now()),
)

note_links = Table(
    "note_links",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("from_note_id", Integer, ForeignKey("notes.id"), nullable=False),
    Column("to_note_id", Integer, ForeignKey("notes.id"), nullable=False),
    Column("reason", Text, nullable=False, server_default=""),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint("from_note_id", "to_note_id", name="uq_note_link"),
)

topics = Table(
    "topics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("name", String(200), nullable=False),
    Column("summary", Text, nullable=False, server_default=""),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

note_topics = Table(
    "note_topics",
    metadata,
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
)

# 使用者在設定頁註冊的 LLM provider（見 reference/backend/llm-integration.md §5）；每帳號各自一套
llm_providers = Table(
    "llm_providers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("name", String(100), nullable=False),
    Column("provider", String(20), nullable=False),  # openai / ollama
    Column("base_url", String(300), nullable=False),
    Column("model", String(200), nullable=False),
    Column("api_key", String(300), nullable=False, server_default=""),
    Column("temperature", Float, nullable=False, server_default="0.7"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

# 導師對話記錄（thread：main＝主頁對話、note:<id>＝聚焦單篇筆記的對話）
chat_messages = Table(
    "chat_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("thread", String(50), nullable=False, server_default="main"),
    Column("role", String(20), nullable=False),  # user / assistant
    Column("content", Text, nullable=False, server_default=""),
    Column("payload", JSON, nullable=True),  # assistant 的 {suggestions, actions}
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

# 生成並保存的心智圖（心智圖頁查看/編輯/重新生成/下載）
mindmaps = Table(
    "mindmaps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("title", String(200), nullable=False),
    Column("markdown", Text, nullable=False),
    # 生成範圍（重新生成時取材用）：topic_id＝主題、query＝自訂描述，皆空＝全部靈感
    Column("topic_id", Integer, nullable=True),
    Column("query", String(300), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

# 導師對話的壓縮摘要（上下文接近上限時自動 compact，舊訊息併入摘要）
chat_summaries = Table(
    "chat_summaries",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("thread", String(50), primary_key=True),
    Column("summary", Text, nullable=False, server_default=""),
    Column("covered_until_id", Integer, nullable=False, server_default="0"),
)

# 每日導師簡報快取（每帳號每天只生成一次）
briefings = Table(
    "briefings",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("date", String(10), primary_key=True),  # YYYY-MM-DD
    Column("payload", JSON, nullable=False),
)

# 全域鍵值設定（目前選用的 chat / embedding provider id）
app_settings = Table(
    "app_settings",
    metadata,
    Column("key", String(100), primary_key=True),
    Column("value", String(500), nullable=False, server_default=""),
)


def run_light_migrations(engine) -> None:
    """輕量遷移：對既有開發庫補「新增的欄位」（已存在會失敗 → 略過）。
    create_all 只建新表、不會改舊表，欄位變更靠這裡；正式環境之後改用 Alembic。"""
    from sqlalchemy import text

    for ddl in (
        "ALTER TABLE mindmaps ADD COLUMN topic_id INTEGER",
        "ALTER TABLE mindmaps ADD COLUMN query VARCHAR(300)",
    ):
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception:  # noqa: BLE001 - 欄位已存在
            pass
