import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

EMAIL = "24f2001074@ds.study.iitm.ac.in"

# Assigned origin + exam origin
ALLOWED_ORIGINS = [
    "https://app-62eqyn.example.com",
    "https://exam.sanand.workers.dev",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

WINDOW = 10
LIMIT = 13
rate_limits = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    origin = request.headers.get("origin")

    # ---------- PRE-FLIGHT ----------
    if request.method == "OPTIONS":
        response = Response(status_code=204)

        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"

        return response

    # ---------- RATE LIMIT ----------
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    bucket = rate_limits.setdefault(client, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= LIMIT:
        return Response(
            status_code=429,
            content="Rate limit exceeded"
        )

    bucket.append(now)

    # ---------- REQUEST CONTEXT ----------
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin

    return response


from fastapi.responses import JSONResponse

@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    response = JSONResponse(
        {
            "email": EMAIL,
            "request_id": request_id
        }
    )

    response.headers["X-Request-ID"] = request_id

    return response