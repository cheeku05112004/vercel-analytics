import json
import math
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

with open(DATA_FILE, encoding="utf-8") as f:
    DATA = json.load(f)


@app.post("/api/latency")
async def latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    result = {}

    for region in regions:
        records = [r for r in DATA if r["region"] == region]

        if not records:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue

        latencies = sorted(float(r["latency_ms"]) for r in records)
        uptimes = [float(r["uptime_pct"]) for r in records]

        p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": latencies[p95_index],
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(x > threshold for x in latencies),
        }

    return result
