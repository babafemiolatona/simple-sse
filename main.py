from fastapi import FastAPI, Request, BackgroundTasks
import asyncio
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware


app = FastAPI()

origins = ["*"]

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


process_queue = asyncio.Queue()

@app.get("/sse-test")
async def sse_task_test(request: Request):
    process_queue = asyncio.Queue()
    
    async def sse_generator():
        # Send an initial message immediately
        yield {"data": "Connection established", "event": "progress"}
        
        try:
            while True:
                data = await process_queue.get()
                if data == "done":
                    yield {"data": "Process completed", "event": "complete"}
                    break
                elif isinstance(data, dict):
                    yield data  # Pass through dictionaries directly
                else:
                    yield {"data": data, "event": "progress"}
        except Exception as e:
            yield {"data": f"Error: {str(e)}", "event": "error"}

    async def background_task():
        try:
            # Send a few messages with delays
            await process_queue.put("Task started")
            
            for i in range(3):
                await asyncio.sleep(1)
                await process_queue.put(f"Processing step {i+1}")
            
            await process_queue.put({"data": "All steps completed", "event": "success"})
            await process_queue.put("done")
        except Exception as e:
            await process_queue.put({"data": f"Task error: {str(e)}", "event": "error"})
            await process_queue.put("done")
    
    # Start background task
    task = asyncio.create_task(background_task())
    request.state.background_tasks = task
    
    # Return streaming response
    return EventSourceResponse(sse_generator(), media_type="text/event-stream")