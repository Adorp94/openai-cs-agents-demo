import json
import os
import sys
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging

# Import modules directly since they're now in the same directory
try:
    from main import (
        triage_agent,
        promoselect_agent,
        suitup_agent,
        create_initial_context,
        PromoProAgentContext,
    )
    
    from agents import (
        Runner,
        ItemHelpers,
        MessageOutputItem,
        HandoffOutputItem,
        ToolCallItem,
        ToolCallOutputItem,
        InputGuardrailTripwireTriggered,
        Handoff,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Available files: {os.listdir('.')}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory store for conversation state (for serverless, this resets between calls)
# In production, you'd want to use a persistent store like Redis or DynamoDB
conversations: Dict[str, Dict[str, Any]] = {}

def _get_agent_by_name(name: str):
    """Return the agent object by name."""
    agents = {
        triage_agent.name: triage_agent,
        promoselect_agent.name: promoselect_agent,
        suitup_agent.name: suitup_agent,
    }
    return agents.get(name, triage_agent)

def _get_guardrail_name(g) -> str:
    """Extract a friendly guardrail name."""
    name_attr = getattr(g, "name", None)
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    guard_fn = getattr(g, "guardrail_function", None)
    if guard_fn is not None and hasattr(guard_fn, "__name__"):
        return guard_fn.__name__.replace("_", " ").title()
    fn_name = getattr(g, "__name__", None)
    if isinstance(fn_name, str) and fn_name:
        return fn_name.replace("_", " ").title()
    return str(g)

def _parse_separate_messages(text: str) -> List[str]:
    """Parse formatted tool result and extract individual messages."""
    messages = []
    lines = text.split('\n')
    
    for line in lines:
        # Look for message patterns (MENSAJE 1A:, MENSAJE 1B:, etc.)
        if line.strip().startswith('MENSAJE ') and ':' in line:
            # Extract the message content after the colon
            message_content = line.split(':', 1)[1].strip()
            if message_content:
                messages.append(message_content)
    
    return messages

def _build_agents_list() -> List[Dict[str, Any]]:
    """Build a list of all available agents and their metadata."""
    def make_agent_dict(agent):
        return {
            "name": agent.name,
            "description": getattr(agent, "handoff_description", ""),
            "handoffs": [getattr(h, "agent_name", getattr(h, "name", "")) for h in getattr(agent, "handoffs", [])],
            "tools": [getattr(t, "name", getattr(t, "__name__", "")) for t in getattr(agent, "tools", [])],
            "input_guardrails": [_get_guardrail_name(g) for g in getattr(agent, "input_guardrails", [])],
        }
    return [
        make_agent_dict(triage_agent),
        make_agent_dict(promoselect_agent),
        make_agent_dict(suitup_agent),
    ]

def process_chat(conversation_id: Optional[str], message: str) -> Dict[str, Any]:
    """Process chat message and return response."""
    # Initialize or retrieve conversation state
    is_new = not conversation_id or conversation_id not in conversations
    
    if is_new:
        conversation_id = uuid4().hex
        ctx = create_initial_context()
        current_agent_name = triage_agent.name
        state = {
            "input_items": [],
            "context": ctx,
            "current_agent": current_agent_name,
        }
        
        if message.strip() == "":
            conversations[conversation_id] = state
            return {
                "conversation_id": conversation_id,
                "current_agent": current_agent_name,
                "messages": [],
                "events": [],
                "context": ctx.dict(),
                "agents": _build_agents_list(),
                "guardrails": [],
            }
    else:
        state = conversations[conversation_id]

    current_agent = _get_agent_by_name(state["current_agent"])
    state["input_items"].append({"content": message, "role": "user"})
    old_context = state["context"].dict().copy()
    guardrail_checks = []

    try:
        # Run the agent asynchronously
        import asyncio
        result = asyncio.run(Runner.run(current_agent, state["input_items"], context=state["context"]))
    except InputGuardrailTripwireTriggered as e:
        failed = e.guardrail_result.guardrail
        gr_output = e.guardrail_result.output.output_info
        gr_reasoning = getattr(gr_output, "reasoning", "")
        gr_input = message
        gr_timestamp = time.time() * 1000
        
        for g in current_agent.input_guardrails:
            guardrail_checks.append({
                "id": uuid4().hex,
                "name": _get_guardrail_name(g),
                "input": gr_input,
                "reasoning": (gr_reasoning if g == failed else ""),
                "passed": (g != failed),
                "timestamp": gr_timestamp,
            })
            
        refusal = "Sorry, I can only answer questions related to promotional products."
        state["input_items"].append({"role": "assistant", "content": refusal})
        
        return {
            "conversation_id": conversation_id,
            "current_agent": current_agent.name,
            "messages": [{"content": refusal, "agent": current_agent.name}],
            "events": [],
            "context": state["context"].model_dump() if hasattr(state["context"], "model_dump") else state["context"].dict(),
            "agents": _build_agents_list(),
            "guardrails": guardrail_checks,
        }

    messages = []
    events = []

    # Process result items
    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            
            # Check if this is a tool result with special formatting instructions for separate messages
            if "IMPORTANTE: Envía cada mensaje por separado" in text:
                # Parse and split into separate messages
                separate_messages = _parse_separate_messages(text)
                for msg in separate_messages:
                    if msg.strip():  # Only add non-empty messages
                        messages.append({"content": msg.strip(), "agent": item.agent.name})
                        events.append({
                            "id": uuid4().hex,
                            "type": "message", 
                            "agent": item.agent.name,
                            "content": msg.strip()
                        })
            else:
                # Normal single message handling
                messages.append({"content": text, "agent": item.agent.name})
                events.append({
                    "id": uuid4().hex,
                    "type": "message",
                    "agent": item.agent.name,
                    "content": text
                })
                
        elif isinstance(item, HandoffOutputItem):
            # Record the handoff event
            events.append({
                "id": uuid4().hex,
                "type": "handoff",
                "agent": item.source_agent.name,
                "content": f"{item.source_agent.name} -> {item.target_agent.name}",
                "metadata": {
                    "source_agent": item.source_agent.name,
                    "target_agent": item.target_agent.name
                },
            })
            
            # Handle handoff callback logic
            from_agent = item.source_agent
            to_agent = item.target_agent
            ho = next(
                (h for h in getattr(from_agent, "handoffs", [])
                 if isinstance(h, Handoff) and getattr(h, "agent_name", None) == to_agent.name),
                None,
            )
            if ho:
                fn = ho.on_invoke_handoff
                fv = fn.__code__.co_freevars
                cl = fn.__closure__ or []
                if "on_handoff" in fv:
                    idx = fv.index("on_handoff")
                    if idx < len(cl) and cl[idx].cell_contents:
                        cb = cl[idx].cell_contents
                        cb_name = getattr(cb, "__name__", repr(cb))
                        events.append({
                            "id": uuid4().hex,
                            "type": "tool_call",
                            "agent": to_agent.name,
                            "content": cb_name,
                        })
            current_agent = item.target_agent
            
        elif isinstance(item, ToolCallItem):
            tool_name = getattr(item.raw_item, "name", None)
            raw_args = getattr(item.raw_item, "arguments", None)
            tool_args = raw_args
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args)
                except Exception:
                    pass
                    
            events.append({
                "id": uuid4().hex,
                "type": "tool_call",
                "agent": item.agent.name,
                "content": tool_name or "",
                "metadata": {"tool_args": tool_args},
            })
            
            # Special handling for business selector
            if tool_name == "display_business_selector":
                messages.append({
                    "content": "DISPLAY_BUSINESS_SELECTOR",
                    "agent": item.agent.name,
                })
                
        elif isinstance(item, ToolCallOutputItem):
            events.append({
                "id": uuid4().hex,
                "type": "tool_output",
                "agent": item.agent.name,
                "content": str(item.output),
                "metadata": {"tool_result": item.output},
            })

    # Handle context changes
    new_context = state["context"].dict()
    changes = {k: new_context[k] for k in new_context if old_context.get(k) != new_context[k]}
    if changes:
        events.append({
            "id": uuid4().hex,
            "type": "context_update",
            "agent": current_agent.name,
            "content": "",
            "metadata": {"changes": changes},
        })

    # Update state
    state["input_items"] = result.to_input_list()
    state["current_agent"] = current_agent.name
    conversations[conversation_id] = state

    # Build guardrail results
    final_guardrails = []
    for g in getattr(current_agent, "input_guardrails", []):
        name = _get_guardrail_name(g)
        failed = next((gc for gc in guardrail_checks if gc.get("name") == name), None)
        if failed:
            final_guardrails.append(failed)
        else:
            final_guardrails.append({
                "id": uuid4().hex,
                "name": name,
                "input": message,
                "reasoning": "",
                "passed": True,
                "timestamp": time.time() * 1000,
            })

    return {
        "conversation_id": conversation_id,
        "current_agent": current_agent.name,
        "messages": messages,
        "events": events,
        "context": state["context"].dict(),
        "agents": _build_agents_list(),
        "guardrails": final_guardrails,
    }

# Vercel serverless function handler
def handler(request):
    """Main handler for Vercel serverless function."""
    
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    # Only allow POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        if hasattr(request, 'json'):
            request_data = request.json
        else:
            body = request.get_body() if hasattr(request, 'get_body') else request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            request_data = json.loads(body)
        
        # Extract request parameters
        conversation_id = request_data.get('conversation_id')
        message = request_data.get('message', '')

        # Process the chat request
        response_data = process_chat(conversation_id, message)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        } 