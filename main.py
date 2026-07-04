import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

EMAIL = "24f2001074@ds.study.iitm.ac.in"

ASSIGNED_ORIGIN = "https://app-62eqyn.example.com"
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

WINDOW = 10
LIMIT = 13

app = FastAPI()

# Let FastAPI handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ASSIGNED_ORIGIN,
        EXAM_ORIGIN,
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

buckets = {}


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    bucket = buckets.setdefault(client, [])

    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= LIMIT:
        response = Response(status_code=429)
        response.headers["Retry-After"] = "10"
        response.headers["X-Request-ID"] = request_id
        return response

    bucket.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):

    response = JSONResponse(
        {
            "email": EMAIL,
            "request_id": request.state.request_id,
        }
    )

    response.headers["X-Request-ID"] = request.state.request_id

    return response