from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict


@dataclass
class SubAgent:
    name: str
    instruction: str
    handler: Callable[[str], str]


@dataclass
class SubAgentManager:
    """Register and dispatch isolated sub-agents (task tool analogue)."""

    registry: Dict[str, SubAgent] = field(default_factory=dict)
    allow_subagent_spawn: bool = False

    def register(self, name: str, instruction: str, handler: Callable[[str], str]) -> None:
        """注册一个子代理及其处理函数。"""
        self.registry[name] = SubAgent(name=name, instruction=instruction, handler=handler)

    def spawn_agent(self, *_: object, **__: object) -> None:
        """显式禁止子代理创建新的代理实例，避免代理树失控扩张。"""
        if not self.allow_subagent_spawn:
            raise PermissionError("Sub-agent 无权创建新 agent，必须由主 agent 统一管理与分配。")

    def task(self, name: str, task_input: str) -> str:
        """调用指定子代理处理任务输入并返回结果。"""
        if name not in self.registry:
            raise KeyError(f"Unknown subagent: {name}")
        return self.registry[name].handler(task_input)
