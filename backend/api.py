from fastapi import FastAPI

app = FastAPI()


@app.get("/api/route-graph")
async def get_route_graph():
    return {
        "connection": "connected",
        "message": "Route graph data will be returned here.",
    }
