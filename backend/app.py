import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.analysis import TicketAnalyzer
from backend.config import load_settings
from backend.ollama_client import OllamaModelClient
from backend.schemas import AnalysisResponse, TicketRequest

logger = logging.getLogger("tinydesk")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

ROOT = Path(__file__).resolve().parents[1]
MAX_REQUEST_BYTES = 200_000

FIELD_LABELS = {
    "id": "ticket number",
    "subject": "subject",
    "description": "description",
    "requester": "requester",
    "department": "department",
    "category": "category",
    "priority": "priority",
    "status": "status",
    "resolutionNote": "resolution note",
    "activity": "activity history",
}

app = FastAPI(title="TinyDesk", docs_url=None, redoc_url=None, openapi_url=None)


def get_model_client() -> OllamaModelClient:
    return OllamaModelClient(load_settings())


def validation_message(exc: RequestValidationError) -> str:
    labels: list[str] = []
    for error in exc.errors():
        parts = [str(part) for part in error.get("loc", ()) if part != "body"]
        key = parts[0] if parts else ""
        label = FIELD_LABELS.get(key, "request")
        if label not in labels:
            labels.append(label)
    if not labels or labels == ["request"]:
        return "This ticket could not be analyzed because the request was not valid."
    if len(labels) == 1:
        return f"This ticket could not be analyzed because the {labels[0]} is missing or not valid."
    joined = ", ".join(labels)
    return f"This ticket could not be analyzed because these fields are missing or not valid: {joined}."


@app.exception_handler(RequestValidationError)
async def reject_invalid_ticket(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = validation_message(exc)
    labels = []
    for error in exc.errors():
        parts = [str(part) for part in error.get("loc", ()) if part != "body"]
        key = parts[0] if parts else "request"
        label = FIELD_LABELS.get(key, "request")
        if label not in labels:
            labels.append(label)
    logger.warning(
        "ticket analysis rejected reason=invalid_request fields=%s",
        ",".join(labels),
    )
    return JSONResponse(status_code=422, content={"available": False, "message": message})


@app.middleware("http")
async def limit_analyze_body(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/api/analyze-ticket":
        raw_length = request.headers.get("content-length")
        if raw_length is not None:
            try:
                size = int(raw_length)
            except ValueError:
                size = MAX_REQUEST_BYTES + 1
            if size > MAX_REQUEST_BYTES:
                logger.warning("ticket analysis rejected reason=request_too_large")
                return JSONResponse(
                    status_code=413,
                    content={
                        "available": False,
                        "message": "This ticket is too large to analyze.",
                    },
                )
    return await call_next(request)


@app.post(
    "/api/analyze-ticket",
    response_model=AnalysisResponse,
    response_model_exclude_none=True,
)
def analyze_ticket(
    ticket: TicketRequest,
    model: OllamaModelClient = Depends(get_model_client),
) -> AnalysisResponse:
    try:
        return TicketAnalyzer(model).analyze(ticket)
    except Exception as exc:
        logger.error(
            "ticket analysis failed reason=unhandled error_type=%s",
            type(exc).__name__,
        )
        return AnalysisResponse(
            available=False,
            message="Analysis could not be completed. Try again.",
        )


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/index.html")
def serve_index_file() -> FileResponse:
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/favicon.svg")
def serve_favicon() -> FileResponse:
    return FileResponse(ROOT / "favicon.svg", media_type="image/svg+xml")


app.mount("/css", StaticFiles(directory=ROOT / "css"), name="css")
app.mount("/js", StaticFiles(directory=ROOT / "js"), name="js")
