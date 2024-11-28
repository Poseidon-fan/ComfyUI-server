from enum import Enum

from sqlalchemy import Index, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from config import RDB_HOST, RDB_NAME, RDB_PASSWORD, RDB_PORT, RDB_USERNAME

_url = f"postgresql+psycopg://{RDB_USERNAME}:{RDB_PASSWORD}@{RDB_HOST}:{RDB_PORT}/{RDB_NAME}"
sql_engine = create_async_engine(_url, pool_pre_ping=True)

Base = declarative_base()


class ErrorCode(Enum):
    SUCCESS = 0
    COMFYUI_QUEUE_PROMPT_ERROR = 1
    S3_UPLOAD_ERROR = 2
    COMFYUI_RETRIEVE_IMAGE_ERROR = 3
    UNKNOWN_ERROR = 10


class ComfyUIRecord(Base):
    __tablename__ = "comfyui_records"
    __table_args__ = (Index("idx_comfyui_task_id", "comfyui_task_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_task_id: Mapped[str] = mapped_column(String)
    client_callback_url: Mapped[str] = mapped_column(String)
    comfyui_task_id: Mapped[str | None] = mapped_column(String)
    comfyui_filepath: Mapped[str | None] = mapped_column(String)
    s3_key: Mapped[str | None] = mapped_column(String)
    error_code: Mapped[ErrorCode | None] = mapped_column(
        Integer,
        nullable=True,
        default=ErrorCode.SUCCESS.value,
        server_default=str(ErrorCode.SUCCESS.value),
    )

    def to_dict(self):
        result = {}
        for key, value in vars(self).items():
            if key.startswith("_"):
                continue
            if isinstance(value, ErrorCode):
                result[key] = value.value
            else:
                result[key] = value
        return result

    def __repr__(self):
        return (
            f"<Record(client_task_id={self.client_task_id}, comfyui_task_id={self.comfyui_task_id}, "
            f"comfyui_path={self.comfyui_filepath}, s3_key={self.s3_key})>"
        )


def init_rdb():
    engine = create_engine(_url, echo=True, pool_pre_ping=True)
    with engine.begin() as conn:
        # Base.metadata.drop_all(conn)
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
        Base.metadata.create_all(conn)
