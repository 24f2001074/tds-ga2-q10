import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "24f2001074@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-62eqyn.example.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-62eqyn.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

WINDOW = 10
LIMIT = 13
buckets = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    # Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Rate limiting
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    bucket = buckets.setdefault(client, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= LIMIT:
        response = Response(status_code=429)
        response.headers["X-Request-ID"] = request_id
        return response

    bucket.append(now)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    response = JSONResponse(
        {
            "email": EMAIL,
            "request_id": request_id,
        }
    )

    response.headers["X-Request-ID"] = request_id
    return response