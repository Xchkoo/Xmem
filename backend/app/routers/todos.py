from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[schemas.TodoOut])
async def list_todos(
    completed: Optional[bool] = Query(None, description="筛选已完成/未完成，None 表示全部"),
    session: AsyncSession = Depends(get_session), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取待办事项列表
    如果 completed=None，返回所有待办（用于待办页面）
    如果 completed=False，只返回未完成的（用于主界面）
    """
    query = select(models.Todo).where(models.Todo.user_id == current_user.id)
    
    if completed is not None:
        query = query.where(models.Todo.completed == completed)
    
    # 只获取组标题或单个待办（group_id 为 None 的）
    query = query.where(models.Todo.group_id.is_(None))
    
    # 按置顶优先，然后按创建时间倒序排序（最新的在上面）
    query = query.order_by(models.Todo.is_pinned.desc(), models.Todo.created_at.desc())
    
    # 使用 selectinload 预加载子待办
    query = query.options(selectinload(models.Todo.group_items))
    
    result = await session.execute(query)
    todos = result.scalars().all()
    
    # 获取所有待办的 ID，用于查询子待办
    todo_ids = [todo.id for todo in todos]
    
    # 一次性查询所有子待办
    if todo_ids:
        group_items_query = select(models.Todo).where(
            models.Todo.group_id.in_(todo_ids),
            models.Todo.user_id == current_user.id
        )
        if completed is not None:
            group_items_query = group_items_query.where(models.Todo.completed == completed)
        group_items_query = group_items_query.order_by(models.Todo.group_id, models.Todo.created_at.asc())
        
        group_items_result = await session.execute(group_items_query)
        all_group_items = group_items_result.scalars().all()
        
        # 按 group_id 分组
        group_items_dict = {}
        for item in all_group_items:
            if item.group_id not in group_items_dict:
                group_items_dict[item.group_id] = []
            group_items_dict[item.group_id].append(item)
    else:
        group_items_dict = {}
    
    # 构建返回数据
    result_list = []
    for todo in todos:
        # 获取子待办（如果存在）
        group_items = None
        if todo.id in group_items_dict:
            group_items_list = group_items_dict[todo.id]
            # 构建子待办的 TodoOut 对象
            group_items = [
                schemas.TodoOut(
                    id=item.id,
                    title=item.title,
                    completed=item.completed,
                    is_pinned=item.is_pinned,
                    group_id=item.group_id,
                    created_at=item.created_at,
                    group_items=None
                )
                for item in group_items_list
            ]
        
        # 手动构建 TodoOut，明确传递所有字段，避免 Pydantic 自动访问关系
        todo_data = schemas.TodoOut(
            id=todo.id,
            title=todo.title,
            completed=todo.completed,
            is_pinned=todo.is_pinned,
            group_id=todo.group_id,
            created_at=todo.created_at,
            group_items=group_items
        )
        
        result_list.append(todo_data)
    
    return result_list


@router.post("", response_model=schemas.TodoOut)
async def create_todo(
    payload: schemas.TodoCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    # 如果指定了 group_id，验证组是否存在且属于当前用户
    if payload.group_id:
        group_result = await session.execute(
            select(models.Todo).where(
                models.Todo.id == payload.group_id,
                models.Todo.user_id == current_user.id,
                models.Todo.group_id.is_(None)  # 确保是组标题，不是子待办
            )
        )
        group = group_result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="组不存在")
    
    todo = models.Todo(
        user_id=current_user.id, 
        title=payload.title,
        group_id=payload.group_id
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    
    # 手动构建 TodoOut，避免 Pydantic 自动访问关系
    return schemas.TodoOut(
        id=todo.id,
        title=todo.title,
        completed=todo.completed,
        is_pinned=todo.is_pinned,
        group_id=todo.group_id,
        created_at=todo.created_at,
        group_items=None  # 新创建的待办不会有子待办
    )


@router.patch("/{todo_id}", response_model=schemas.TodoOut)
async def update_todo(
    todo_id: int,
    payload: schemas.TodoUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """更新待办事项（标题或完成状态）"""
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    
    # 更新标题
    if payload.title is not None:
        todo.title = payload.title
    
    # 更新完成状态
    if payload.completed is not None:
        todo.completed = payload.completed
        
        # 如果待办被标记为完成，自动取消置顶
        if payload.completed:
            todo.is_pinned = False
        
        # 如果是组内的待办，检查组是否应该完成
        if todo.group_id:
            # 检查组内所有待办是否都完成
            group_items_result = await session.execute(
                select(models.Todo).where(
                    models.Todo.group_id == todo.group_id,
                    models.Todo.user_id == current_user.id
                )
            )
            group_items = group_items_result.scalars().all()
            
            # 获取组标题
            group_result = await session.execute(
                select(models.Todo).where(
                    models.Todo.id == todo.group_id,
                    models.Todo.user_id == current_user.id
                )
            )
            group = group_result.scalars().first()
            
            if group and group_items:
                # 检查是否所有子待办都完成
                all_completed = all(item.completed for item in group_items)
                group.completed = all_completed
        # 如果是组标题，检查子待办状态
        elif not todo.group_id:
            # 检查是否有子待办
            group_items_result = await session.execute(
                select(models.Todo).where(
                    models.Todo.group_id == todo.id,
                    models.Todo.user_id == current_user.id
                )
            )
            group_items = group_items_result.scalars().all()
            
            if group_items:
                # 组标题的完成状态由所有子待办决定
                all_completed = all(item.completed for item in group_items)
                todo.completed = all_completed
                # 如果组标题被标记为完成，自动取消置顶
                if all_completed:
                    todo.is_pinned = False
    
    await session.commit()
    await session.refresh(todo)
    
    # 如果是组标题，需要加载子待办
    group_items = None
    if not todo.group_id:
        # 检查是否有子待办
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items_list = group_items_result.scalars().all()
        if group_items_list:
            group_items = [
                schemas.TodoOut(
                    id=item.id,
                    title=item.title,
                    completed=item.completed,
                    is_pinned=item.is_pinned,
                    group_id=item.group_id,
                    created_at=item.created_at,
                    group_items=None
                )
                for item in sorted(group_items_list, key=lambda x: x.created_at, reverse=True)
            ]
    
    # 手动构建 TodoOut，避免 Pydantic 自动访问关系
    return schemas.TodoOut(
        id=todo.id,
        title=todo.title,
        completed=todo.completed,
        is_pinned=todo.is_pinned,
        group_id=todo.group_id,
        created_at=todo.created_at,
        group_items=group_items
    )


@router.patch("/{todo_id}/toggle", response_model=schemas.TodoOut)
async def toggle_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """切换待办完成状态（保持向后兼容）"""
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    
    # 切换完成状态
    new_completed = not todo.completed
    todo.completed = new_completed
    
    # 如果待办被标记为完成，自动取消置顶
    if new_completed:
        todo.is_pinned = False
    
    # 如果是组标题，同时切换所有子待办的状态
    if not todo.group_id:
        # 检查是否有子待办
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items = group_items_result.scalars().all()
        
        if group_items:
            # 同时切换所有子待办的状态
            for item in group_items:
                item.completed = new_completed
    
    # 如果是组内的待办，检查组是否应该完成
    elif todo.group_id:
        # 检查组内所有待办是否都完成
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.group_id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items = group_items_result.scalars().all()
        
        # 获取组标题
        group_result = await session.execute(
            select(models.Todo).where(
                models.Todo.id == todo.group_id,
                models.Todo.user_id == current_user.id
            )
        )
        group = group_result.scalars().first()
        
        if group and group_items:
            # 检查是否所有子待办都完成
            all_completed = all(item.completed for item in group_items)
            group.completed = all_completed
            # 如果组标题被标记为完成，自动取消置顶
            if all_completed:
                group.is_pinned = False
    # 如果是组标题，检查子待办状态
    elif not todo.group_id:
        # 检查是否有子待办
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items = group_items_result.scalars().all()
        
        if group_items:
            # 组标题的完成状态由所有子待办决定
            all_completed = all(item.completed for item in group_items)
            todo.completed = all_completed
            # 如果组标题被标记为完成，自动取消置顶
            if all_completed:
                todo.is_pinned = False
    
    await session.commit()
    await session.refresh(todo)
    
    # 如果是组标题，需要加载子待办
    group_items = None
    if not todo.group_id:
        # 检查是否有子待办
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items_list = group_items_result.scalars().all()
        if group_items_list:
            group_items = [
                schemas.TodoOut(
                    id=item.id,
                    title=item.title,
                    completed=item.completed,
                    is_pinned=item.is_pinned,
                    group_id=item.group_id,
                    created_at=item.created_at,
                    group_items=None
                )
                for item in sorted(group_items_list, key=lambda x: x.created_at, reverse=True)
            ]
    
    # 手动构建 TodoOut，避免 Pydantic 自动访问关系
    return schemas.TodoOut(
        id=todo.id,
        title=todo.title,
        completed=todo.completed,
        is_pinned=todo.is_pinned,
        group_id=todo.group_id,
        created_at=todo.created_at,
        group_items=group_items
    )


@router.patch("/{todo_id}/pin", response_model=schemas.TodoOut)
async def toggle_pin_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """切换待办的置顶状态"""
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    
    # 只允许置顶组标题或单个待办，不允许置顶组内待办
    if todo.group_id:
        raise HTTPException(status_code=400, detail="组内待办不能置顶")
    
    todo.is_pinned = not todo.is_pinned
    await session.commit()
    await session.refresh(todo)
    
    # 如果是组标题，需要加载子待办
    group_items = None
    if not todo.group_id:
        # 检查是否有子待办
        group_items_result = await session.execute(
            select(models.Todo).where(
                models.Todo.group_id == todo.id,
                models.Todo.user_id == current_user.id
            )
        )
        group_items_list = group_items_result.scalars().all()
        if group_items_list:
            group_items = [
                schemas.TodoOut(
                    id=item.id,
                    title=item.title,
                    completed=item.completed,
                    is_pinned=item.is_pinned,
                    group_id=item.group_id,
                    created_at=item.created_at,
                    group_items=None
                )
                for item in sorted(group_items_list, key=lambda x: x.created_at, reverse=True)
            ]
    
    # 手动构建 TodoOut，避免 Pydantic 自动访问关系
    return schemas.TodoOut(
        id=todo.id,
        title=todo.title,
        completed=todo.completed,
        is_pinned=todo.is_pinned,
        group_id=todo.group_id,
        created_at=todo.created_at,
        group_items=group_items
    )


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        # 如果待办不存在，可能是已经被删除（例如级联删除），返回成功而不是 404
        # 这样可以避免前端在删除组时因为组内待办已经被删除而报错
        return {"ok": True}
    
    # 如果删除的是组标题，由于设置了 cascade="all, delete-orphan"，子待办会自动删除
    # 如果删除的是组内待办，直接删除
    await session.delete(todo)
    await session.commit()
    return {"ok": True}

