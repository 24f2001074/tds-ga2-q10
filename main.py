import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

EMAIL = "24f2001074@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-62eqyn.example.com"

app = FastAPI()

WINDOW = 10
LIMIT = 13
buckets = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    origin = request.headers.get("Origin")

    # Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Handle preflight
    if request.method == "OPTIONS":
        response = Response(status_code=204)

        if origin:
            # Allow assigned origin OR browser origin (exam page)
            if origin == ALLOWED_ORIGIN or origin.startswith("http"):
                response.headers["Access-Control-Allow-Origin"] = origin

            response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

        response.headers["X-Request-ID"] = request_id
        return response

    # Rate limiting
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    bucket = buckets.setdefault(client, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= LIMIT:
        response = Response(status_code=429)

        response.headers["X-Request-ID"] = request_id

    if origin == ALLOWED_ORIGIN or origin == "https://exam.sanand.workers.dev":
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

    return response

    bucket.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    if origin:
        if origin == ALLOWED_ORIGIN or origin.startswith("http"):
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

    return response


@app.get("/ping")
async def ping(request: Request):
    return JSONResponse(
        {
            "email": EMAIL,
            "request_id": request.state.request_id,
        },
        headers={
            "X-Request-ID": request.state.request_id
        }
    )