"""Loyihalar API — CRUD, loyihaga bog'langan vazifalar va progress."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import case, func, select, update

from app.api.deps import BossUser, CurrentUser, SessionDep
from app.core.constants import Role, TaskType
from app.models import Project, Task
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectOut, ProjectUpdate
from app.services import board_service, task_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: CurrentUser, session: SessionDep):
    stmt = select(Project).order_by(Project.created_at.desc())
    if user.role == Role.WORKER:
        stmt = stmt.where(
            Project.id.in_(
                select(Task.project_id).where(
                    Task.project_id.is_not(None), Task.masul_id == user.id
                )
            )
        )
    result = await session.execute(stmt)
    projects = list(result.scalars().all())
    if not projects:
        return []

    done_keys = await board_service.get_done_keys(session)
    is_done = Task.status.in_(done_keys) if done_keys else False
    counts_result = await session.execute(
        select(
            Task.project_id,
            func.count().label("total"),
            func.sum(case((is_done, 1), else_=0)).label("done"),
        )
        .where(Task.project_id.is_not(None))
        .group_by(Task.project_id)
    )
    counts = {row.project_id: (row.total, row.done or 0) for row in counts_result.all()}

    out_list = []
    for project in projects:
        out = ProjectOut.model_validate(project)
        total, done = counts.get(project.id, (0, 0))
        out.task_count = total
        out.done_count = done
        out.percent = round(done * 100 / total) if total else 0
        out_list.append(out)
    return out_list


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: int, user: CurrentUser, session: SessionDep):
    project = await _get_or_404(session, project_id)
    stmt = select(Task).where(Task.project_id == project_id)
    if user.role == Role.WORKER:
        stmt = stmt.where(Task.masul_id == user.id)
    stmt = stmt.order_by(Task.created_at)
    result = await session.execute(stmt)
    tasks = list(result.scalars().all())
    if user.role == Role.WORKER and not tasks:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bu loyihada sizga tegishli ish yo'q")
    done_keys = await board_service.get_done_keys(session)

    from app.api.routers.tasks import _to_out_batch

    out = ProjectDetail.model_validate(project)
    out.tasks = await _to_out_batch(session, tasks, done_keys)
    out.task_count = len(tasks)
    out.done_count = sum(1 for t in tasks if t.status in done_keys)
    out.percent = round(out.done_count * 100 / out.task_count) if out.task_count else 0
    return out


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, boss: BossUser, session: SessionDep):
    project = Project(name=body.name, description=body.description, created_by=boss.id)
    session.add(project)
    await session.flush()

    from app.schemas.task import TaskCreate

    for work in body.tasks:
        if not work.name.strip():
            continue
        await task_service.create_task(
            session,
            TaskCreate(
                name=work.name,
                dep_id=work.dep_id,
                masul_id=work.masul_id,
                type=TaskType.STANDALONE,
                project_id=project.id,
            ),
            created_by=boss.id,
        )

    return await get_project(project.id, boss, session)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int, body: ProjectUpdate, _: BossUser, session: SessionDep
):
    project = await _get_or_404(session, project_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await session.flush()

    detail = await get_project(project_id, _, session)
    out = ProjectOut.model_validate(project)
    out.task_count = detail.task_count
    out.done_count = detail.done_count
    out.percent = detail.percent
    return out


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, _: BossUser, session: SessionDep):
    project = await _get_or_404(session, project_id)
    await session.execute(
        update(Task).where(Task.project_id == project_id).values(project_id=None)
    )
    await session.delete(project)


async def _get_or_404(session: SessionDep, project_id: int) -> Project:
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Loyiha topilmadi")
    return project
