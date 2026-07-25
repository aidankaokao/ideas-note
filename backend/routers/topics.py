from fastapi import APIRouter, Depends

from routers.deps import get_current_user
from services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
def list_topics(user: dict = Depends(get_current_user)):
    return topic_service.list_topics(user["id"])
