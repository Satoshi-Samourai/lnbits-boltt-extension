import asyncio

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import boltt_generic_router
from .views_api import boltt_api_router
from .views_lnurl import boltt_lnurl_router


class LNURLErrorResponseHandler(APIRoute):
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                response = await original_route_handler(request)
            except HTTPException as exc:
                logger.debug(f"HTTPException: {exc}")
                response = JSONResponse(
                    status_code=exc.status_code,
                    content={"status": "ERROR", "reason": f"{exc.detail}"},
                )
            except Exception as exc:
                raise exc

            return response

        return custom_route_handler


boltt_ext: APIRouter = APIRouter(prefix="/boltt", tags=["BOLTT"], route_class=LNURLErrorResponseHandler)
boltt_ext.include_router(boltt_generic_router)
boltt_ext.include_router(boltt_api_router)
boltt_ext.include_router(boltt_lnurl_router)

boltt_static_files = [
    {
        "path": "/boltt/static",
        "name": "boltt_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def boltt_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def boltt_start():
    task = create_permanent_unique_task("ext_boltt", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = ["db", "boltt_ext", "boltt_static_files", "boltt_start", "boltt_stop"]
