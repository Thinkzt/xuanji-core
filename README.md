# XuanJi Agent Core 🐲

> 璇玑Agent Core - 新claw超级架构
> 多线程、高性能、分布式AI Agent框架

## 概述

璇玑Agent Core是璇玑史诗自主研发的下一代AI Agent框架，旨在替代OpenClaw，实现真正的多线程、高性能、分布式架构。

### 核心特性

| 特性 | 说明 |
|------|------|
| 多线程Actor模型 | 每个Agent独立运行，通过消息队列通信 |
| Skill动态加载 | 运行时动态加载/卸载Skill |
| Tool并行执行 | 多个Tool并行执行，提高效率 |
| 三层解耦架构 | 接入层/计算层/状态层完全解耦 |
| 集群部署 | 支持多节点分布式部署 |

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    璇玑Agent Core                           │
├─────────────────────────────────────────────────────────────┤
│  接入层 (Gateway)     │  多协议支持：WebSocket/HTTP/gRPC   │
├───────────────────────┼────────────────────────────────────┤
│  计算层 (Compute)     │  多线程Actor + 消息队列            │
├───────────────────────┼────────────────────────────────────┤
│  状态层 (State)       │  Redis集群 + SQLite本地备份        │
└───────────────────────┴────────────────────────────────────┘
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
import asyncio
from xuanji_core import AgentManager, Message, MessageType, Priority

async def main():
    # 创建Agent管理器
    manager = AgentManager()
    
    # 创建Agent
    agent = manager.create_agent("main", "主控Agent")
    await manager.start_agent("main")
    
    # 发送心跳
    await agent.send(Message(
        type=MessageType.HEARTBEAT,
        sender="demo",
        priority=Priority.P0_URGENT
    ))
    
    # 等待处理
    await asyncio.sleep(1)
    
    # 查看Agent状态
    print(manager.list_agents())

asyncio.run(main())
```

## 项目结构

```
xuanji_core/
├── src/
│   ├── __init__.py          # 包入口
│   ├── actor.py              # 核心Actor模型
│   ├── router.py             # 消息路由器
│   ├── gateway.py             # 接入层网关
│   └── state.py              # 状态层管理
├── tests/
│   └── test_actor.py         # 单元测试
├── docs/
│   └── CLAW_ARCH_v1.md       # 架构设计文档
├── requirements.txt           # 依赖列表
├── README.md                  # 本文件
└── LICENSE                    # MIT License
```

## 开发计划

| 阶段 | 任务 | 状态 |
|------|------|------|
| Phase 1 | 核心Actor模型 + 消息队列 | ✅ 完成 |
| Phase 2 | Skill动态加载机制 | 🔄 进行中 |
| Phase 3 | Tool并行执行器 | ⏳ 待开始 |
| Phase 4 | 接入层网关 | ⏳ 待开始 |
| Phase 5 | 状态层(Redis) | ⏳ 待开始 |
| Phase 6 | 集群部署 | ⏳ 待开始 |

## 设计原则

1. **零bug交付** - 所有功能必须有测试
2. **禁止屎山** - 代码必须可维护、可扩展
3. **文档完善** - 每个模块必须有docstring
4. **类型提示** - 必须使用type hint

## License

MIT License - 璇玑史诗

---

**🐲 璇玑Agent Core - 重新定义AI Agent框架**
