"""Local localhost-only bridge for Flutter/Android <-> Termux Agent."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from agent.core.agent import Agent
from agent.memory.store import MemoryStore
from agent.tools.builtin import build_tools
from agent.tools.registry import Tool, ToolRegistry

app = FastAPI(title="MyChatBot Bridge", version="0.2.0")
store = MemoryStore(os.getenv("MYCHATBOT_DATA", "runtime")); registry = ToolRegistry()
handlers = build_tools(store)

SCHEMAS = {
 "list_files":{"type":"object","properties":{"path":{"type":"string"}}},
 "read_file":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]},
 "write_file":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]},
 "delete_file":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]},
 "terminal":{"type":"object","properties":{"command":{"type":"string"},"timeout":{"type":"integer","minimum":1,"maximum":120}},"required":["command"]},
 "memory_search":{"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]},
 "memory_save":{"type":"object","properties":{"kind":{"type":"string"},"content":{"type":"string"}},"required":["content"]},
 "skill_list":{"type":"object","properties":{}},
 "skill_read":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]},
 "skill_save":{"type":"object","properties":{"name":{"type":"string"},"content":{"type":"string"}},"required":["name","content"]},
 "wifi_manager":{"type":"object","properties":{}},"network_info":{"type":"object","properties":{}},"connectivity":{"type":"object","properties":{}},
 "ping":{"type":"object","properties":{"host":{"type":"string"},"count":{"type":"integer","minimum":1,"maximum":4}}},
 "dns_lookup":{"type":"object","properties":{"host":{"type":"string"}},"required":["host"]},
 "traceroute":{"type":"object","properties":{"host":{"type":"string"}}},"wifi_interface_info":{"type":"object","properties":{}},
 "wifi_scan":{"type":"object","properties":{}},
 "network_scan":{"type":"object","properties":{"cidr":{"type":"string","description":"Only a network the user owns or is authorized to assess."}}},
 "wifite_detect":{"type":"object","properties":{}},"wifite_tool":{"type":"object","properties":{"action":{"type":"string","enum":["audit"]}}},
 "system_info":{"type":"object","properties":{}},"battery":{"type":"object","properties":{}},"storage_info":{"type":"object","properties":{}},
 "zip_info":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]},
 "zip_extract":{"type":"object","properties":{"path":{"type":"string"},"destination":{"type":"string"}},"required":["path"]},
}
for name, fn in handlers.items():
    registry.register(Tool(name, f"MyChatBot {name} tool. Use only for the user's device/network and obey permission policy.", SCHEMAS.get(name,{"type":"object","properties":{}}), fn))
agent = Agent(registry, store); pending: dict[str, tuple[str,dict]] = {}

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    provider: str | None = None
    model: str | None = None
    history: list[dict] = Field(default_factory=list)
class ConfirmRequest(BaseModel):
    id: str = Field(min_length=8, max_length=200)
    approve: bool

@app.get('/health')
def health():
    return {'status':'ok','provider':os.getenv('AI_PROVIDER','openai'),'model':os.getenv('AI_MODEL','gpt-5.6-luna'),'bridge':'localhost-only'}

@app.get('/tools')
def tools(): return {'tools':registry.definitions(),'count':len(registry.definitions())}

@app.get('/permissions/{tool_name}')
def permissions(tool_name:str):
    if not registry.get(tool_name): raise HTTPException(404,'Unknown tool')
    return registry.permission(tool_name,{})

@app.post('/chat')
def chat(req:ChatRequest):
    try:
        result=agent.run(req.message,req.provider,req.model,req.history)
        for item in result.get('pending') or []: pending[item['id']] = (item['name'],item['arguments'])
        return result
    except KeyError as exc: raise HTTPException(503,f'Missing configuration: {exc}')
    except Exception as exc: raise HTTPException(500,f'Agent error: {exc}')

@app.post('/confirm')
def confirm(req:ConfirmRequest):
    action=pending.pop(req.id,None)
    if action is None: raise HTTPException(404,'Confirmation expired or not found')
    if not req.approve: return {'ok':True,'cancelled':True,'content':'Operation cancelled.'}
    name,args=action; result=registry.execute(name,args,confirmed=True)
    return {'ok':result.get('ok',False),'tool':name,**result}
