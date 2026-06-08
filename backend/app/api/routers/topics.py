"""Bildirishnoma mavzulari (topic) — admin nomlab boshqaradi (faqat boshliq)."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import BossUser, SessionDep
from app.models import Topic
from app.schemas.topic import TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
async def list_topics(_: BossUser, session: SessionDep):
    result = await session.execute(select(Topic).order_by(Topic.id))
    return list(result.scalars().all())


@router.post("", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
async def create_topic(body: TopicCreate, _: BossUser, session: SessionDep):
    topic = Topic(**body.model_dump())
    session.add(topic)
    await session.flush()
    return topic


@router.patch("/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: int, body: TopicUpdate, _: BossUser, session: SessionDep):
    topic = await _get_or_404(session, topic_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: int, _: BossUser, session: SessionDep):
    topic = await _get_or_404(session, topic_id)
    await session.delete(topic)


async def _get_or_404(session: SessionDep, topic_id: int) -> Topic:
    topic = await session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mavzu topilmadi")
    return topic
