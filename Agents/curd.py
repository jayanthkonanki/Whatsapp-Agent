import pandas as pd
import os
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext 
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import logfire
import asyncio
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# ==========================================
# 1. THE DATABASE LAYER (The "World")
# ==========================================
DB_FILE = r"C:\Users\jkona\OneDrive\Documents\Jayanth\Whatsapp-Agent\Agents\employees.xlsx"

def load_db():
    """Reads the Excel file or creates a new one if missing."""
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["ID", "Name", "Role", "Salary"])
        df.to_excel(DB_FILE, index=False)
        return df
    return pd.read_excel(DB_FILE)

def save_db(df):
    """Atomic save to Excel."""
    df.to_excel(DB_FILE, index=False)

# ==========================================
# 2. THE SCHEMA / CONTRACTS (Pydantic Models)
# ==========================================
# These classes automatically generate the JSON Schema for the LLM.
# They are the "Instructions" on how to use the tools.

class CreateEmployee(BaseModel):
    id: int = Field(..., description="Unique numeric ID for the new employee.")
    name: str = Field(..., description="Full name of the employee.")
    role: str = Field(..., description="Job title (e.g., Developer, HR).")
    salary: int = Field(..., gt=0, description="Annual salary. Must be positive.")

class UpdateEmployee(BaseModel):
    id: int = Field(..., description="The ID of the employee to update.")
    column: str = Field(..., description="Column to change: 'Name', 'Role', or 'Salary'.")
    value: str | int = Field(..., description="The new value to insert.")

class DeleteEmployee(BaseModel):
    id: int = Field(..., description="The ID of the employee to remove.")

class SearchQuery(BaseModel):
    query: str = Field(..., description="The name or role to search for (RAG).")

# ==========================================
# 3. THE AGENT SETUP
# ==========================================
# Initialize the agent. Replace with your model provider.
# If using OpenRouter, use 'openai:upstage/solar-pro-3-free' etc.
logfire.configure()

'''model = OpenRouterModel(
    'meta-llama/llama-3.3-70b-instruct:free',
    provider=OpenRouterProvider(api_key='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'),
)'''



model = OpenAIChatModel(
    'qwen3-coder:480b-cloud',
    provider=OpenAIProvider(
        base_url='http://localhost:11434/v1', api_key='ollama'
    ),
)

agent = Agent(
    model, 
    system_prompt=(
        "You are an Excel Database Manager. "
        "1. ALWAYS Search (Read) before you Update or Delete to confirm IDs. "
        "2. Never guess IDs. "
        "3. If a user asks to add someone, check if the ID exists first."
    )
)

# ==========================================
# 4. THE TOOLS (The "Hands")
# ==========================================

# --- READ (RAG / Search) ---
@agent.tool
def read_database(ctx: RunContext, search: SearchQuery) -> str:
    """
    Searches the database for a name, role, or ID. 
    Use this to find the 'Context' before taking action.
    """
    df = load_db()
    
    # Simple search logic: Check if query exists in any column
    mask = df.astype(str).apply(lambda x: x.str.contains(search.query, case=False)).any(axis=1)
    results = df[mask]
    print('read')
    if results.empty:
        return "No records found matching that query."
    
    return results.to_markdown(index=False)

# --- CREATE ---
@agent.tool
def add_employee(ctx: RunContext, emp: CreateEmployee) -> str:
    """Adds a new row to the Excel sheet."""
    df = load_db()
    
    print('add')
    if emp.id in df["id"].values:
        return f"Error: ID {emp.id} already exists. Please choose a different ID."
    
    new_row = pd.DataFrame([emp.model_dump()])
    df = pd.concat([df, new_row], ignore_index=True)
    save_db(df)
    return f"Success: Added {emp.name} (ID: {emp.id})."

# --- UPDATE ---
@agent.tool
def update_employee(ctx: RunContext, update: UpdateEmployee) -> str:
    """Updates a single cell for a specific employee ID."""
    df = load_db()

    print('update')
    if update.id not in df["id"].values:
        return f"Error: ID {update.id} not found. Use 'read_database' to find the correct ID."
    
    if update.column not in df.columns:
        return f"Error: Column '{update.column}' does not exist."

    # Update logic
    df.loc[df["id"] == update.id, update.column] = update.value
    save_db(df)
    return f"Success: Updated {update.column} for ID {update.id} to {update.value}."

# --- DELETE ---
@agent.tool
def delete_employee(ctx: RunContext, target: DeleteEmployee) -> str:
    """Removes an entire row based on ID."""
    df = load_db()
    
    if target.id not in df["id"].values:
        return f"Error: ID {target.id} not found."
    
    # Delete logic: Keep everything EXCEPT the target ID
    df = df[df["id"] != target.id]
    save_db(df)
    return f"Success: Deleted employee with ID {target.id}."

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":

    
    try:
        query = input('Enter Query')
        while query !='stop':

        # run_sync returns a RunResult object
            result = agent.run_sync(query)
        # Accessing the final response text
        # In pydantic-ai, the result of the model is in .data
            print(f"\n🤖 Agent Response:\n{result.output}")
            query = input('Enter Query else enter stop')
        
    except Exception as e:
        print(f"Error: {e}")
        # Debugging: print what attributes ARE available
        if 'result' in locals():
            print(f"Available attributes: {dir(result)}")