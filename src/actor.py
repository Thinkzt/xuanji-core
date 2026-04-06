#!/usr/bin/env python3
"""
璇玑Agent Core - 核心Actor模型 v1.0
多线程、高性能、分布式AI Agent框架

设计目标：替代OpenClaw，实现真正的多线程Agent架构
"""

import asyncio
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import threading


# ============== 核心枚举 ==============

class Priority(Enum):
    """消息优先级"""
    P0_URGENT = 0   # 紧急：异常告警、紧急任务
    P1_HIGH = 1     # 高优先：普通任务、定时任务
    P2_NORMAL = 2   # 普通：批量处理
    P3_LOW = 3      # 低优先：日志、统计

class MessageType(Enum):
    """消息类型"""
    EXECUTE_TASK = "execute_task"
    LOAD_SKILL = "load_skill"
    REGISTER_TOOL = "register_tool"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    RESULT = "result"
    ERROR = "error"

# ============== 核心数据结构 ==============

@dataclass
class Message:
    """Actor消息"""
    type: MessageType
    payload: Any
    priority: Priority = Priority.P2_NORMAL
    sender: str = ""
    target: str = ""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """优先级比较"""
        return self.priority.value < other.priority.value

@dataclass
class Task:
    """任务定义"""
    task_id: str
    skill: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timeout: int = 30  # 默认30秒超时

@dataclass
class Result:
    """执行结果"""
    task_id: str
    success: bool
    data: Any = None
    error: str = ""
    duration: float = 0.0

# ============== 核心Actor ==============

class AgentActor:
    """
    独立Agent执行单元
    
    每个Agent是一个独立的Actor，拥有：
    - 私有消息队列
    - 独立状态
    - 已加载的Skill列表
    - 可用的Tool列表
    """
    
    def __init__(self, agent_id: str, name: str = ""):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.mailbox: asyncio.PriorityQueue[Message] = asyncio.PriorityQueue()
        self.state: Dict[str, Any] = {}
        self.skills: Dict[str, Any] = {}
        self.tools: Dict[str, Callable] = {}
        self.status = "initializing"
        self.created_at = time.time()
        self.task_count = 0
        self.error_count = 0
        self._running = False
        self._lock = threading.Lock()
        
    def __repr__(self):
        return f"AgentActor({self.agent_id}, status={self.status}, tasks={self.task_count})"
    
    async def start(self):
        """启动Actor"""
        self.status = "running"
        self._running = True
        print(f"✅ {self} 已启动")
        asyncio.create_task(self._process_messages())
        asyncio.create_task(self._heartbeat())
    
    async def stop(self):
        """停止Actor"""
        self.status = "stopping"
        self._running = False
        self.status = "stopped"
        print(f"🛑 {self} 已停止")
    
    async def send(self, message: Message):
        """发送消息到Mailbox"""
        await self.mailbox.put(message)
    
    async def _send_response(self, target: str, message: Message):
        """发送响应消息到目标Agent"""
        # 简化实现：打印日志，生产环境应通过Router发送
        print(f"📤 {self} -> {target}: {message.type.value}")
    
    async def _process_messages(self):
        """消息处理循环"""
        while self._running:
            try:
                message = await asyncio.wait_for(self.mailbox.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ {self} 消息处理异常: {e}")
    
    async def _handle_message(self, message: Message):
        """处理不同类型的消息"""
        handlers = {
            MessageType.EXECUTE_TASK: self._handle_execute_task,
            MessageType.LOAD_SKILL: self._handle_load_skill,
            MessageType.REGISTER_TOOL: self._handle_register_tool,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.SHUTDOWN: self._handle_shutdown,
        }
        
        handler = handlers.get(message.type)
        if handler:
            await handler(message)
        else:
            print(f"⚠️ {self} 未知消息类型: {message.type}")
    
    async def _handle_execute_task(self, message: Message):
        """执行任务"""
        task: Task = message.payload
        self.task_count += 1
        
        start_time = time.time()
        try:
            # 查找Skill
            skill = self.skills.get(task.skill)
            if not skill:
                raise ValueError(f"Skill不存在: {task.skill}")
            
            # 执行Action
            action = skill.get(task.action)
            if not action:
                raise ValueError(f"Action不存在: {task.action}")
            
            # 带超时执行
            result = await asyncio.wait_for(
                action(task.params, task.context),
                timeout=task.timeout
            )
            
            duration = time.time() - start_time
            result_obj = Result(
                task_id=task.task_id,
                success=True,
                data=result,
                duration=duration
            )
            
            # 发送结果到发送者
            await self._send_response(message.sender, Message(
                type=MessageType.RESULT,
                payload=result_obj,
                sender=self.agent_id,
                target=message.sender,
                priority=Priority.P0_URGENT
            ))
            
        except asyncio.TimeoutError:
            self.error_count += 1
            duration = time.time() - start_time
            print(f"⏰ {self} 任务超时: {task.task_id}")
            
        except Exception as e:
            self.error_count += 1
            duration = time.time() - start_time
            print(f"❌ {self} 任务失败: {task.task_id} - {e}")
    
    async def _handle_load_skill(self, message: Message):
        """加载Skill"""
        skill_data = message.payload
        skill_name = skill_data.get("name")
        skill_module = skill_data.get("module")
        
        try:
            # 动态加载模块
            import importlib
            module = importlib.import_module(skill_module)
            
            # 注册到skills字典
            self.skills[skill_name] = {
                "module": module,
                "actions": getattr(module, "ACTIONS", {}),
                "loaded_at": time.time()
            }
            
            print(f"✅ {self} Skill加载成功: {skill_name}")
            
        except Exception as e:
            print(f"❌ {self} Skill加载失败: {skill_name} - {e}")
    
    async def _handle_register_tool(self, message: Message):
        """注册Tool"""
        tool_name = message.payload.get("name")
        tool_func = message.payload.get("func")
        
        with self._lock:
            self.tools[tool_name] = tool_func
            print(f"✅ {self} Tool注册: {tool_name}")
    
    async def _handle_heartbeat(self, message: Message):
        """心跳响应"""
        await self._send_response(message.sender, Message(
            type=MessageType.RESULT,
            payload={
                "agent_id": self.agent_id,
                "status": self.status,
                "task_count": self.task_count,
                "error_count": self.error_count,
                "skills": list(self.skills.keys()),
                "tools": list(self.tools.keys()),
                "uptime": time.time() - self.created_at
            },
            sender=self.agent_id,
            target=message.sender,
            priority=Priority.P0_URGENT
        ))
    
    async def _handle_shutdown(self, message: Message):
        """关闭处理"""
        await self.stop()
    
    async def _heartbeat(self):
        """定期心跳"""
        while self._running:
            await asyncio.sleep(30)  # 30秒心跳
            print(f"💓 {self} 存活，运行时间: {time.time() - self.created_at:.0f}s")

# ============== Agent Manager ==============

class AgentManager:
    """
    Agent管理器 - 管理所有Agent的生命周期
    
    职责：
    - 创建/销毁Agent
    - 路由消息到对应Agent
    - 监控Agent健康状态
    - 负载均衡
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentActor] = {}
        self.lock = threading.Lock()
        print("🚀 AgentManager 已初始化")
    
    def create_agent(self, agent_id: str, name: str = "") -> AgentActor:
        """创建Agent"""
        with self.lock:
            if agent_id in self.agents:
                print(f"⚠️ Agent已存在: {agent_id}")
                return self.agents[agent_id]
            
            agent = AgentActor(agent_id, name)
            self.agents[agent_id] = agent
            print(f"✅ Agent创建: {agent_id}")
            return agent
    
    async def start_agent(self, agent_id: str):
        """启动Agent"""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.start()
        else:
            print(f"❌ Agent不存在: {agent_id}")
    
    async def stop_agent(self, agent_id: str):
        """停止Agent"""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.stop()
    
    def get_agent(self, agent_id: str) -> Optional[AgentActor]:
        """获取Agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有Agent"""
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "status": a.status,
                "task_count": a.task_count,
                "skills": list(a.skills.keys()),
                "uptime": time.time() - a.created_at
            }
            for a in self.agents.values()
        ]
    
    async def broadcast(self, message: Message):
        """广播消息到所有Agent"""
        for agent in self.agents.values():
            if agent.status == "running":
                await agent.send(message)

# ============== 消息路由器 ==============

class MessageRouter:
    """
    消息路由器 - 根据消息目标路由到对应Agent
    """
    
    def __init__(self, manager: AgentManager):
        self.manager = manager
        self.routes: Dict[str, str] = {}  # target -> agent_id
    
    def register_route(self, target: str, agent_id: str):
        """注册路由"""
        self.routes[target] = agent_id
    
    async def route(self, message: Message):
        """路由消息"""
        target_agent = message.target or "default"
        agent_id: str = self.routes.get(target_agent) or ""
        
        if not agent_id:
            # 默认路由到第一个可用Agent
            agents = list(self.manager.agents.values())
            if agents:
                agent_id = agents[0].agent_id
        
        if not agent_id:
            print(f"❌ 路由失败: 无可用Agent")
            return
            
        agent = self.manager.get_agent(agent_id)
        if agent and agent.status == "running":
            await agent.send(message)
        else:
            print(f"❌ 路由失败: 无可用Agent {agent_id}")

# ============== 演示主函数 ==============

async def demo():
    """演示：创建Agent并执行任务"""
    print("=" * 60)
    print(" 璇玑Agent Core 演示")
    print("=" * 60)
    
    # 创建Manager
    manager = AgentManager()
    router = MessageRouter(manager)
    
    # 创建主Agent
    main_agent = manager.create_agent("main", "主控Agent")
    await manager.start_agent("main")
    
    # 注册路由
    router.register_route("main", "main")
    
    # 模拟加载Skill
    async def demo_action(params, context):
        await asyncio.sleep(0.5)  # 模拟处理
        return {"result": "success", "input": params}
    
    # 创建测试Skill模块
    class DemoSkill:
        ACTIONS = {"process": demo_action}
    
    # 加载Skill
    await main_agent.send(Message(
        type=MessageType.LOAD_SKILL,
        payload={"name": "demo", "module": "xuanji_core.src.actor"},
        priority=Priority.P2_NORMAL
    ))
    
    # 注册Tool
    await main_agent.send(Message(
        type=MessageType.REGISTER_TOOL,
        payload={"name": "echo", "func": lambda x: x},
        priority=Priority.P2_NORMAL
    ))
    
    # 发送心跳
    await main_agent.send(Message(
        type=MessageType.HEARTBEAT,
        sender="demo_sender",
        priority=Priority.P0_URGENT
    ))
    
    # 等待处理
    await asyncio.sleep(2)
    
    # 列出所有Agent
    print("\n📊 Agent列表:")
    for agent_info in manager.list_agents():
        print(f"  {agent_info}")
    
    # 关闭
    await manager.stop_agent("main")
    print("\n✅ 演示完成")

if __name__ == "__main__":
    asyncio.run(demo())
