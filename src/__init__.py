"""
璇玑Agent Core - 新claw超级架构
多线程、高性能、分布式AI Agent框架

版本: v1.0.0
日期: 2026-04-06
"""

from .actor import (
    AgentActor,
    AgentManager,
    MessageRouter,
    Message,
    MessageType,
    Task,
    Result,
    Priority
)

__version__ = "1.0.0"
__all__ = [
    "AgentActor",
    "AgentManager", 
    "MessageRouter",
    "Message",
    "MessageType",
    "Task",
    "Result",
    "Priority"
]
