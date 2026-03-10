from fastapi import FastAPI

from services import say_hello

app = FastAPI(title="MCP-IS-PROJECT", version="0.1.0")


@app.get("/")
async def root(name: str = "World") -> dict:
    return {"message": say_hello(name)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
