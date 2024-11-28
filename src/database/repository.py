from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from database import ComfyUIRecord, sql_engine


class RecordRepository:
    @staticmethod
    async def create(comfyui_record: ComfyUIRecord) -> ComfyUIRecord:
        async_session = async_sessionmaker(sql_engine)
        async with async_session() as session:
            session.add(comfyui_record)
            await session.commit()
            await session.refresh(comfyui_record)
        return comfyui_record

    @staticmethod
    async def retrieve_by_comfyui_task_id(comfy_task_id: str) -> ComfyUIRecord:
        async_session = async_sessionmaker(sql_engine)
        async with async_session() as session:
            stmt = select(ComfyUIRecord).where(ComfyUIRecord.comfyui_task_id == comfy_task_id)
            result = await session.execute(stmt)
            record = result.scalars().first()
            return record

    @staticmethod
    async def update(comfyui_record: ComfyUIRecord) -> ComfyUIRecord:
        async_session = async_sessionmaker(sql_engine)
        async with async_session() as session:
            session.add(comfyui_record)
            await session.commit()
            await session.refresh(comfyui_record)
        return comfyui_record
