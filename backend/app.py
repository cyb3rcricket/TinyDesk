import logging
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.analysis import TicketAnalyzer
from backend.config import load_settings
from backend.ollama_client import ModelCallError, OllamaModelClient
from backend.xai_client import XaiModelClient
from backend.schemas import AnalysisResponse, TicketRequest

logger = logging.getLogger("tinydesk")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG_FILE = ROOT / ".env"
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


class RejectingModelClient:
    """Used when TINYDESK_AI_PROVIDER is set to a name this server does not know."""

    def complete(self, *, model: str, messages: list[dict], schema: dict, timeout: float) -> str:
        raise ModelCallError("bad_config", "UnknownProvider")


def assistant_description(settings) -> dict:
    """Non-secret provider facts for the assistant panel.

    The response names the product and whether analysis sends ticket text.
    It does not include credentials, model settings, or request headers.
    """
    if settings.provider == "ollama":
        return {
            "provider": "ollama",
            "placement": "local",
            "product": "Ollama",
            "sendsTicketToProvider": False,
        }
    if settings.provider == "xai":
        return {
            "provider": "xai",
            "placement": "cloud",
            "product": "xAI Grok",
            "sendsTicketToProvider": True,
        }
    return {
        "provider": "unrecognized",
        "placement": "unknown",
        "product": "",
        "sendsTicketToProvider": False,
    }


def get_model_client() -> OllamaModelClient | XaiModelClient | RejectingModelClient:
    settings = load_settings()
    if settings.provider == "xai" and settings.config_error:
        logger.info(
            "analysis provider=%s model=%s config_error=%s",
            settings.provider,
            settings.model,
            settings.config_error,
        )
    elif settings.provider == "xai":
        logger.info(
            "analysis provider=%s model=%s reasoning_effort=%s max_completion_tokens=%s",
            settings.provider,
            settings.model,
            settings.reasoning_effort,
            settings.max_completion_tokens,
        )
    else:
        logger.info("analysis provider=%s model=%s", settings.provider, settings.model)
    if settings.provider == "xai":
        return XaiModelClient(settings)
    if settings.provider == "ollama":
        return OllamaModelClient(settings)
    return RejectingModelClient()


def invalid_field_labels(exc: RequestValidationError) -> list[str]:
    labels: list[str] = []
    for error in exc.errors():
        parts = [str(part) for part in error.get("loc", ()) if part != "body"]
        key = parts[0] if parts else ""
        label = FIELD_LABELS.get(key, "request")
        if label not in labels:
            labels.append(label)
    return labels


def validation_message(exc: RequestValidationError) -> str:
    labels = invalid_field_labels(exc)
    if not labels or labels == ["request"]:
        return "This ticket could not be analyzed because the request was not valid."
    if len(labels) == 1:
        return f"This ticket could not be analyzed because the {labels[0]} is missing or not valid."
    joined = ", ".join(labels)
    return f"This ticket could not be analyzed because these fields are missing or not valid: {joined}."


@app.exception_handler(RequestValidationError)
async def reject_invalid_ticket(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = validation_message(exc)
    labels = invalid_field_labels(exc)
    logger.warning(
        "ticket analysis rejected reason=invalid_request fields=%s",
        ",".join(labels),
    )
    return JSONResponse(status_code=422, content={"available": False, "message": message})


def request_targets_local_config(path: str) -> bool:
    """True when a URL path points at the git-ignored local config file."""
    if not path:
        return False
    config = LOCAL_CONFIG_FILE.resolve()
    candidates = [path]
    decoded = unquote(path)
    if decoded != path:
        candidates.append(decoded)
    for candidate in candidates:
        if ".env" in PurePosixPath(candidate).parts:
            return True
        relative = candidate.lstrip("/")
        if not relative or "\x00" in relative or relative.startswith(("/", "\\")):
            continue
        try:
            resolved = (ROOT / relative).resolve()
        except (OSError, ValueError):
            continue
        if resolved == config:
            return True
    return False


@app.middleware("http")
async def hide_local_config(request: Request, call_next):
    raw_path = request.scope.get("path", "")
    if request_targets_local_config(raw_path) or request_targets_local_config(request.url.path):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return await call_next(request)


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


@app.get("/api/assistant")
def assistant_metadata() -> dict:
    return assistant_description(load_settings())


@app.post(
    "/api/analyze-ticket",
    response_model=AnalysisResponse,
    response_model_exclude_none=True,
)
def analyze_ticket(
    ticket: TicketRequest,
    model: OllamaModelClient | XaiModelClient | RejectingModelClient = Depends(get_model_client),
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
