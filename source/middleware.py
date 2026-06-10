from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .planner import TodoPlanner


class BaseMiddleware:
    def before(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """主逻辑执行前调用，可用于注入或改写状态。"""
        return state

    def after(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """主逻辑执行后调用，可用于收敛或摘要状态。"""
        return state


@dataclass
class PlanningMiddleware(BaseMiddleware):
    planner: TodoPlanner

    def before(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """将输入中的 proposed_todos 写入规划器。"""
        items: List[str] = state.get("proposed_todos", [])
        if items:
            state["todos"] = self.planner.write_todos(items)
        return state


@dataclass
class SummarizationMiddleware(BaseMiddleware):
    max_messages: int = 8

    def after(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """当消息过长时进行裁剪，并把历史压缩为 summary。"""
        messages: List[str] = state.get("messages", [])
        if len(messages) > self.max_messages:
            old = messages[:-self.max_messages]
            state["summary"] = " | ".join(old)
            state["messages"] = messages[-self.max_messages:]
        return state
