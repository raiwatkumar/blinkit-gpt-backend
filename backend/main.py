from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Optional, List
from groq import Groq
from supabase import create_client, Client
import uvicorn
from fastapi.responses import FileResponse

# Secure API Keys from Environment Variables
GROQ_API_KEY= "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"
SUPABASE_URL= "https://pabuobujcacbuxzralpm.supabase.co"
SUPABASE_KEY= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhYnVvYnVqY2FjYnV4enJhbHBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgwNTgyNTcsImV4cCI6MjA1MzYzNDI1N30.fdrU9nt6faejp_bF8Kmy65-XTn6VmQCc0y-G9Nq-TpA" 

# Ensure API keys exist
if not GROQ_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing API keys. Ensure they are set in the .env file.")

# Initialize FastAPI
app = FastAPI()

# ===== Adding CORS Middleware =====
# This middleware will handle preflight OPTIONS requests and add the necessary headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allows all origins - adjust this in production for security
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)

# Get the path to the backend directory
backend_path = os.getcwd()

# Get the parent directory (project root) and join with 'frontend'
frontend_path = os.path.join(os.path.dirname(backend_path), "frontend")

try:
    if os.path.exists(frontend_path):
        print(f"📁 Mounting frontend directory from: {frontend_path}")
        # Mount static files at /static instead of root /
        app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="frontend")
        
        # Add a root route to serve index.html
        @app.get("/")
        async def serve_index():
            return FileResponse(os.path.join(frontend_path, "index.html"))
    else:
        print(f"⚠️ WARNING: Frontend directory not found at: {frontend_path}")
except Exception as e:
    print(f"❌ Error mounting frontend: {str(e)}")

    
# Pydantic Model for Request Validation
class AnyRequest(BaseModel):
    name: str

def search_item(supabase, search_term: str):
    print(f"Searching for: {search_term}")
    
    # Clean up search term
    search_term = search_term.lower().strip()
    search_term = search_term.split('(')[0].strip()  # Remove anything in parentheses
    
    try:
        # Strategy 1: Exact match
        print(f"Trying exact match for '{search_term}'")
        response = supabase.table('video').select('*').eq('name', search_term).execute()
        if response.data:
            print(f"Found exact match")
            return response.data[0]

        # Strategy 2: ILIKE match
        print(f"Trying partial match for '{search_term}'")
        response = supabase.table('video').select('*').ilike('name', f'%{search_term}%').execute()
        if response.data:
            print(f"Found partial match")
            return response.data[0]

        # Strategy 3: Word-by-word match
        words = search_term.split()
        if len(words) > 1:
            print(f"Trying word-by-word match")
            for word in words:
                if len(word) > 2:  # Skip very short words
                    response = supabase.table('video').select('*').ilike('name', f'%{word}%').execute()
                    if response.data:
                        print(f"Found match using word: '{word}'")
                        return response.data[0]

        print(f"No matches found for: {search_term}")
        return None

    except Exception as e:
        print(f"Error in search_item: {str(e)}")
        return None

@app.post("/process-request/")
async def process_request(request: AnyRequest) -> dict:
    try:
        # Define the System Prompt
        system_prompt = """

You are a **task-based ordering assistant** that helps users order specific items from a quick commerce stores based on the task or plans. Quick commerce stores have dark stores which store items for a short period of time and enable quick delivery. Your role is to:  
1. **Understand the user's task and budget constraints**:
   - Rephrase the task for clarity
   - If the intention is budget-based, note it and prioritize only the essential items
   - Remove emojis or unnecessary words  
2. **Identify and list individual items** required to complete the task. Items should be:
   - Clearly named using standard terminology
   - Ordered by priority (essential items first when the intention is budget-based)
   - Limited to what can be purchased from a quick commerce store
   - Limited to 20 items maximum
3. When the intention of query is budget-based:
   - Prioritize only the Essential items that are crucial for the event without which the event cannot take place.
   - Suggest budget-friendly alternatives when possible
4. **Format the response** precisely as follows:  

```
Task Name: [Clear and formatted task name]  
Items:  
- [Item 1]  
- [Item 2]  
- [...]  
```

In case of a budget, the response should be as follows:

Task Name: [Clear and formatted task name]
Items:
- [item 1]
- [item 2]


Formatting Rules: 
- Use hyphens (`-`) for list items, not asterisks.  
- Ensure correct spelling and terminology.  
- Do not include unnecessary fillers or conversational text.
- Don't add "or" and "optional" items.
- Items in singular form(for e.g., "Cloth" instead of "Clothes")  
- Don't add any other text in the items list apart from the items.
**Examples:**  

#### Example 1 (With Budget)
**User Input:** "I want to throw a birthday party under 800"
**Assistant Output:**
```
Task Name: Birthday Party Planning Under ₹800
Budget: ₹800
Items:
- Birthday cake
- Candles
- Chips
- Cold drinks
- Balloons

#### **Example 2**  
**User Input:** "Planning a weekend BBQ. Need supplies!"  
**Assistant Output:**  
```
Task Name: Weekend BBQ Preparation  
Items:  
- Barbecue griller set  
- Fresh chicken wings  
- Mutton seekh kebab (frozen)  
- Chicken sausages  
- Pav (burger buns)  
- Hot dog buns  
- Cheese slices  
- Pickles  
- Red onions  
- BBQ sauce  
- Mayonnaise  
- Spicy mustard  
- Tomato ketchup  
- Bell peppers  
- Corn on the cob  
- Lettuce  
- Disposable plates  
- Plastic cups  
- Tissue paper  
```
#### **Example 3**  
**User Input:** "Planning a Beach Trip. I am planning a trip under 1500 rupees"  
**Assistant Output:**  
```
Task Name: Beach Trip Packing List
Items:
Sunscreen
Beach towel
Flip-flops
Sunglasses
Water bottle
Snacks
Hat
Swimwear
Beach mat
Waterproof phone pouch


#### **Example 3**  
**User Input:** "Planning a Beach Trip. I am planning a trip under 4000 rupees"  
**Assistant Output:**  
```
Task Name: Beach Trip Packing List
Items:
Beach Towel
Sunscreen Lotion
Beach Umbrella
Waterproof Beach Bag
Flip Flops
Snacks and Water Bottles
Portable Speaker
Beach Toys
Portable Cooler
Sunglasses
Hats
Beach Chair
Wet Wipes
Trash Bags
Portable Power Bank
First Aid Kit
Waterproof Phone Case
Beach Mat
Camera
Beach Blanket
Insect Repellent
Hand Sanitizer
Beach Shoes


Ensure strict adherence to this format.

"""

        # Initialize Groq Client
        client = Groq(api_key=GROQ_API_KEY)

        # Get user input - directly access the name field from the Pydantic model
        user_input = request.name

        # Call Groq API for response
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            model="mixtral-8x7b-32768",
            temperature=0,
            max_tokens=1024
        )

        # Extract the response
        response_text = chat_completion.choices[0].message.content
        print("Groq Raw Response:", response_text)

        # Parse response with new format
        response_lines: List[str] = response_text.split('\n')

        # Extract Task Name (With Fallback)
        task_name: str = next(
            (line.split("Task Name:")[1].strip() for line in response_lines if line.startswith("Task Name:")),
            "Untitled Task"
        )

        # Extract Items List
        items_start: int = next(
            (i for i, line in enumerate(response_lines) if line.lower().strip().startswith("items")),
            -1
        )

        item_names: List[str] = []
        if items_start != -1:
            for line in response_lines[items_start + 1:]:
                line = line.lstrip('*- ').strip()  # Remove bullets
                line = line.split('(')[0].strip()  # Remove parenthetical comments
                if line:
                    item_names.append(line)
                else:
                    break  # Stop at empty line

        print("Parsed Items List:", item_names)

        # Initialize Supabase Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Fetch item details from the database
        items = []
        print("Processing items:")
        for name in item_names:
            print(f"Processing: {name}")
            
            result = search_item(supabase, name)
            
            if result:
                item_data = {
                    'name': name,
                    'quantity': result.get('quantity', "1"),
                    'units': result.get('units', "piece"),
                    'image_url': result.get('url')
                }
                print(f"Added item with details")
            else:
                item_data = {
                    'name': name, 
                    'quantity': "1",
                    'units': "piece",
                    'image_url': None
                }
                print(f"Added item with default values")
            items.append(item_data)

        return {
            "status": "success",
            "task_name": task_name,
            "items": items
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Run the FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
