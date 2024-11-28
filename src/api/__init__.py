from enum import Enum
from typing import Any, Callable

from fastapi import APIRouter
from pydantic import BaseModel

from api.service import Service
from config import ROUTE_PREFIX


class CustomAPIRouter(APIRouter):
    """
    Custom APIRouter that excludes None values from response models by default.
    """

    def get(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().get(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def post(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().post(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def put(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().put(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def delete(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().delete(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def patch(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().patch(path, response_model_exclude_none=response_model_exclude_none, **kwargs)


router = CustomAPIRouter(prefix=ROUTE_PREFIX)


class ServiceType(Enum):
    TEXT2IMG = "text2img"
    IMG2IMG = "img2img"


class RequestDTO(BaseModel):
    service_type: ServiceType
    client_task_id: str
    client_callback_url: str
    params: dict


@router.post("")
async def queue_prompt(request_dto: RequestDTO):
    """commit a prompt to the comfyui server"""
    service_func = getattr(Service, request_dto.service_type.value)
    return await service_func(request_dto.client_task_id, request_dto.client_callback_url, request_dto.params)
