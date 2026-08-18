import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("finez")


def finez_exception_handler(exc, context):
    """
    Wrapper padrão do DRF + log estruturado.

    Nunca loga o corpo bruto da requisição (pode conter amount_cents +
    description juntos) — só tipo de exceção e path.
    """
    response = exception_handler(exc, context)
    request = context.get("request")
    path = getattr(request, "path", "unknown")
    if response is not None:
        logger.warning("api_error", extra={"status": response.status_code, "path": path})
    else:
        logger.error("unhandled_exception", extra={"path": path, "exc_type": type(exc).__name__})
    return response
