from fastapi import FastAPI
from datetime import datetime
app = FastAPI()
@app.get("/")
async def root(): return {"status": "running", "message": "Agent OS V2 Backend"}
