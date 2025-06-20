import asyncio
import uvicorn
import os
import sys

import uvicorn.logging

# Add project root to path so 'backend.src...' imports work
project_root = os.path.abspath(".")  # your progetto-tesi_03 folder
sys.path.insert(0, project_root)

async def run_backend():
    # note the module path to server.py is backend.src.backend.server:app
    config = uvicorn.Config("backend.src.backend.server:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def run_frontend():
    # similarly for frontend
    config = uvicorn.Config("frontend.src.frontend.frontend:app", host="127.0.0.1", port=8001, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(run_backend(), run_frontend())

if __name__ == "__main__":
    asyncio.run(main())
