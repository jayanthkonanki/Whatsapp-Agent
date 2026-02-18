import requests
import json
import os

# ==========================================
# 1. THE CONTRACT (System Prompt)
# ==========================================
# This is the "Constitution" for the agent. It enforces behavior.
SYSTEM_PROMPT = """
You are a precision calculation assistant. 
RULES:
1. You have access to a tools list multiply,sum.
2. If any tool helps to solve user query, you MUST uses the tool. DO NOT calculate it mentally.
3. You must output valid JSON tool calls when requested.
4. If a tool is used, you will receive the result in the next turn. Use that result to answer the user.
"""

# ==========================================
# 2. THE TOOLS & SCHEMA
# ==========================================
def multiply(a, b):
    print('Using Multiplication function')
    return a * b
def sum(a,b):
    print('Using Addition Function')
    return a+b 

available_functions = {
    "multiply": multiply,
    "sum": sum 
}

tools_schema = [

    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "Multiplies two integers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "sum",
            "description": "Addition of two integers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
        }
    }
]

# ==========================================
# 3. THE LLM INTERFACE (Stateless Handler)
# ==========================================
API_KEY = "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" # <--- TODO: Insert Key

def call_llm(full_conversation_history, tools):
    """
    Sends the ENTIRE conversation history to the LLM.
    This is necessary because the LLM has no memory of previous requests.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    payload = {
        "model": "upstage/solar-pro-3:free", # Or "openai/gpt-4o", etc.
        "messages": full_conversation_history, # <--- SENDING ALL MEMORY
        "tools": tools,
        "tool_choice": "auto"
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        print(f"📡 Sending {len(full_conversation_history)} messages to LLM...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        # --- ADAPTER: Normalize response to object notation ---
        data = response.json()
        message_data = data['choices'][0]['message']
        print(message_data)
        class MessageAdapter:
            def __init__(self, msg_dict):
                self.content = msg_dict.get('content')
                self.role = msg_dict.get('role')
                self.tool_calls = []
                
                raw_calls = msg_dict.get('tool_calls', [])
                if raw_calls:
                    for call in raw_calls:
                        self.tool_calls.append(self.ToolCallAdapter(call))
                else:
                    self.tool_calls = None

            class ToolCallAdapter:
                def __init__(self, call_dict):
                    self.id = call_dict.get('id')
                    self.function = self.FunctionAdapter(call_dict.get('function'))

                class FunctionAdapter:
                    def __init__(self, func_dict):
                        self.name = func_dict.get('name')
                        self.arguments = func_dict.get('arguments')

        return MessageAdapter(message_data)

    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

# ==========================================
# 4. THE RUNTIME (State Manager)
# ==========================================
def run_agent(user_query):
    # 1. Initialize Memory with the Contract
    # We MUST start with the system prompt so the LLM knows its role.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}, 
        {"role": "user", "content": user_query}
    ]
    
    # 2. First Pass: Send context to LLM
    llm_response = call_llm(messages, tools_schema)
    
    if not llm_response:
        return "System Error: LLM failed to respond."

    # 3. Check for Tool Use (The "Ticket")
    if llm_response.tool_calls:
        print("🎫 The LLM has issued a tool ticket.")
        
        # CRITICAL STEP: Add the Assistant's "Thought" to memory
        # If we don't do this, the LLM will forget it ever asked for the tool.
        # We must reconstruct the tool_calls object for the history
        messages.append({
            "role": "assistant",
            "content": llm_response.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                } for tc in llm_response.tool_calls
            ]
        })

        # 4. Execute Tools
        for tool_call in llm_response.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Python Executing: {func_name}({args})")
            
            # Run the actual Python code
            result = available_functions[func_name](**args)
            
            # 5. Add Result to Memory (The "Observation")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": str(result)
            })

        # 6. Second Pass: Send UPDATED memory back to LLM
        # The LLM now sees: [System, User, Assistant(Call), Tool(Result)]
        final_response = call_llm(messages, tools_schema)
        return final_response.content
    
    return llm_response.content

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    query = "sum of 50,10"
    print(f"User: {query}")
    answer = run_agent(query)
    print(f"\n🤖 Final Answer: {answer}")