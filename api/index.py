
import json
from pathlib import Path
from math import floor, ceil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
# Read the telemetry JSON file
file_path = (
    Path(__file__).resolve().parent.parent
    / "q-vercel-latency.json"
)

with open(file_path, "r") as f:
    data = json.load(f)


class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: float


def calculate_p95(values):
    values = sorted(values)
    n = len(values)
    position = (n - 1) * 0.95

    lower = floor(position)
    upper = ceil(position)

    return values[lower] + (
        values[upper] - values[lower]
    ) * (position - lower)


@app.get("/")
def home():
    return {"message": "Analytics API is running"}


@app.post("/api/latency")
def analytics(request: RequestData):
    results = {}

    for region in request.regions:
        records = [
            row for row in data
            if row["region"] == region
        ]

        if not records:
            continue

        latencies = [
            row["latency_ms"] for row in records
        ]

        uptimes = [
            row["uptime_pct"] for row in records
        ]

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = calculate_p95(latencies)
        avg_uptime = sum(uptimes) / len(uptimes)

        breaches = sum(
            latency > request.threshold_ms
            for latency in latencies
        )

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return {"regions": results}


