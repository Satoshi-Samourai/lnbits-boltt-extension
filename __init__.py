import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import boltt_generic_router
from .views_api import boltt_api_router
from .views_lnurl import boltt_lnurl_router

logger.debug(
    "This logged message is from boltt/__init__.py, you can debug in your "
    "extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'."
)


boltt_ext: APIRouter = APIRouter(prefix="/boltt", tags=["BOLTT"])
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


__all__ = [
    "db",
    "boltt_ext",
    "boltt_static_files",
    "boltt_start",
    "boltt_stop",
]
