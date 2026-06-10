from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass, field
from json_repair import repair_json
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence


class GuardrailError(Exception):
    """约束层拦截时抛出的异常。"""


@dataclass
class AgentLimits:
    """资源限制参数。"""

    max_calls: int = 8
    max_context_chars: int = 4000
    timeout_seconds: int = 15


@dataclass
class ConstraintLayer:
    """约束层：访问控制、内容过滤、资源限制与风险拦截。"""

    allowed_tools: set[str] = field(default_factory=lambda: {"file_ops", "command_ops", "subagent", "planner"})
    allowed_data_roots: Sequence[str] = (".", "./data", "./workspace")
    sensitive_words: Sequence[str] = (
        "暴力",
        "恐怖",
        "洗钱",
        "色情",
        "自杀",
    )
    privileged_words: Sequence[str] = ("忽略以上", "越权", "提权", "系统提示", "管理员口令")
    high_risk_ops: Sequence[str] = ("rm -rf", "shutdown", "reboot", "mkfs", "dd if=")
    limits: AgentLimits = field(default_factory=AgentLimits)
    _call_count: int = 0

    def reset_budget(self) -> None:
        """重置本轮预算计数。"""
        self._call_count = 0

    def register_call(self) -> None:
        """记录一次调用并检查最大调用次数。"""
        self._call_count += 1
        if self._call_count > self.limits.max_calls:
            raise GuardrailError("超过最大调用次数限制")

    def validate_tool_access(self, tool_name: str) -> None:
        """校验工具调用范围。"""
        if tool_name not in self.allowed_tools:
            raise GuardrailError(f"工具 {tool_name} 不在允许范围")

    def validate_data_access(self, path: str) -> None:
        """校验数据访问路径范围。"""
        if not any(path.startswith(root) for root in self.allowed_data_roots):
            raise GuardrailError(f"数据路径 {path} 不在允许范围")

    def filter_instruction(self, text: str) -> None:
        """过滤敏感词、越权提示与高危操作。"""
        lower = text.lower()
        if any(word in text for word in self.sensitive_words):
            raise GuardrailError("检测到敏感内容，已拦截")
        if any(word in text for word in self.privileged_words):
            raise GuardrailError("检测到越权指令，已拦截")
        if any(op in lower for op in self.high_risk_ops):
            raise GuardrailError("检测到高危操作，已拦截")

    def trim_context(self, messages: List[str]) -> List[str]:
        """限制上下文长度，避免资源滥用。"""
        if sum(len(m) for m in messages) <= self.limits.max_context_chars:
            return messages
        kept: List[str] = []
        total = 0
        for msg in reversed(messages):
            if total + len(msg) > self.limits.max_context_chars:
                break
            kept.append(msg)
            total += len(msg)
        return list(reversed(kept))

    def enforce_timeout(self, started_at: float) -> None:
        """校验执行总时长是否超时。"""
        if time.time() - started_at > self.limits.timeout_seconds:
            raise GuardrailError("执行超时，已终止")

    @staticmethod
    def desensitize(text: str) -> str:
        """对常见隐私字段进行自动脱敏。"""
        text = re.sub(r"\b\d{11}\b", "***********", text)
        text = re.sub(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}", "***@***", text)
        text = re.sub(r"\b\d{17}[0-9Xx]\b", "******************", text)
        return text


@dataclass
class ValidationLayer:
    """校验层：格式、关键词、事实、规则与评分门禁。"""

    required_json_keys: Sequence[str] = ("status", "message", "data", "errors")
    score_threshold: float = 0.6

    def validate_json_schema(self, payload: Dict[str, Any]) -> List[str]:
        """检查输出 JSON 结构完整性。"""
        return [k for k in self.required_json_keys if k not in payload]

    @staticmethod
    def validate_keywords(text: str, required_keywords: Iterable[str]) -> List[str]:
        """检查关键词是否完整。"""
        return [kw for kw in required_keywords if kw not in text]

    @staticmethod
    def validate_facts(text: str, facts: Dict[str, str]) -> List[str]:
        """简单事实性校验：关键事实片段必须出现。"""
        misses: List[str] = []
        for name, snippet in facts.items():
            if snippet and snippet not in text:
                misses.append(name)
        return misses

    @staticmethod
    def validate_rules(state: Dict[str, Any], rules: Sequence[Callable[[Dict[str, Any]], Optional[str]]]) -> List[str]:
        """执行自定义规则校验。"""
        issues: List[str] = []
        for rule in rules:
            msg = rule(state)
            if msg:
                issues.append(msg)
        return issues

    def model_score(self, text: str) -> float:
        """轻量打分：按结构与信息量给出 0~1 分数。"""
        score = 0.0
        if len(text.strip()) > 20:
            score += 0.25
        if any(x in text for x in ("计划", "步骤", "结果", "风险")):
            score += 0.25
        if "\n" in text:
            score += 0.25
        if "{" in text and "}" in text:
            score += 0.25
        return min(score, 1.0)

    def check_score_gate(self, text: str) -> Optional[str]:
        """模型评分门禁。"""
        score = self.model_score(text)
        if score < self.score_threshold:
            return f"模型评分 {score:.2f} 低于阈值 {self.score_threshold:.2f}"
        return None


@dataclass
class CorrectionLayer:
    """纠正层：自动修复、回滚兜底与反馈注入。"""

    fallback_message: str = "系统已触发安全兜底，请提供更明确且合规的输入。"

    def snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """保存状态快照用于失败回滚。"""
        return copy.deepcopy(state)

    def rollback(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """回滚到快照状态。"""
        return copy.deepcopy(snapshot)

    def auto_fix_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """自动修复输出格式，确保 JSON 键完整。"""
        fixed = dict(payload)
        fixed.setdefault("status", "ok")
        fixed.setdefault("message", "")
        fixed.setdefault("data", {})
        fixed.setdefault("errors", [])
        return fixed

    def auto_fix_logic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """自动修复逻辑冲突（例如 progress 与 todos 不一致）。"""
        fixed = dict(payload)
        data = dict(fixed.get("data", {}))
        todos = data.get("todos", [])
        progress = data.get("progress")
        if isinstance(todos, list) and isinstance(progress, str) and "/" in progress:
            left, right = progress.split("/", 1)
            if right.split()[0].isdigit() and int(right.split()[0]) != len(todos):
                done = sum(1 for item in todos if isinstance(item, dict) and item.get("done"))
                data["progress"] = f"{done}/{len(todos)} completed"
        fixed["data"] = data
        return fixed

    def inject_feedback(self, state: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """将错误原因反馈注入到上下文，便于模型重试。"""
        new_state = dict(state)
        msgs = list(new_state.get("messages", []))
        msgs.append(f"system-feedback: {reason}")
        new_state["messages"] = msgs
        return new_state

    def degraded_response(self, reason: str) -> Dict[str, Any]:
        """返回降级兜底响应。"""
        return {
            "status": "degraded",
            "message": self.fallback_message,
            "data": {"reason": reason},
            "errors": [reason],
        }


def normalize_json_output(payload: Dict[str, Any], need = True) -> str:
    """统一输出为 JSON 字符串。"""
    parsed_json = payload.replace("```json", "").replace("```", "")
    if need:
        parsed_json = repair_json(parsed_json, return_objects=True)
    return parsed_json
