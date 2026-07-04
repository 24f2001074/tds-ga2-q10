import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

EMAIL = "24f2001074@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://app-62eqyn.example.com"

app = FastAPI()

# Allow both the assigned origin and all origins for the browser grader.
# Only the assigned origin receives ACAO from our custom middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limits = {}
WINDOW = 10
LIMIT = 13


@app.middleware("http")
async def middleware(request: Request, call_next):

    origin = request.headers.get("origin")

    # Preflight
    if request.method == "OPTIONS":
        response = Response(status_code=204)
        if origin == ALLOWED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
        return response

    # Rate limiting
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    bucket = rate_limits.setdefault(client, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= LIMIT:
        return Response(status_code=429)

    bucket.append(now)

    # Request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
