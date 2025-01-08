# Description: Add your page endpoints here.

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from lnbits.settings import settings

from .crud import get_boltt
from .helpers import lnurler

boltt_generic_router = APIRouter()


def boltt_renderer():
    return template_renderer(["boltt/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page


@boltt_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return boltt_renderer().TemplateResponse(
        "boltt/index.html", {"request": req, "user": user.json()}
    )


# Frontend shareable page


@boltt_generic_router.get("/{boltt_id}")
async def boltt(req: Request, boltt_id):
    myex = await get_boltt(boltt_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )
    return boltt_renderer().TemplateResponse(
        "boltt/boltt.html",
        {
            "request": req,
            "boltt_id": boltt_id,
            "lnurlpay": lnurler(myex.id, "boltt.api_lnurl_pay", req),
            "web_manifest": f"/boltt/manifest/{boltt_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@boltt_generic_router.get("/manifest/{boltt_id}.webmanifest")
async def manifest(boltt_id: str):
    boltt = await get_boltt(boltt_id)
    if not boltt:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )

    return {
        "short_name": settings.lnbits_site_title,
        "name": boltt.name + " - " + settings.lnbits_site_title,
        "icons": [
            {
                "src": (
                    settings.lnbits_custom_logo
                    if settings.lnbits_custom_logo
                    else "https://cdn.jsdelivr.net/gh/lnbits/lnbits@0.3.0/docs/logos/lnbits.png"
                ),
                "type": "image/png",
                "sizes": "900x900",
            }
        ],
        "start_url": "/boltt/" + boltt_id,
        "background_color": "#1F2234",
        "description": "Minimal extension to build on",
        "display": "standalone",
        "scope": "/boltt/" + boltt_id,
        "theme_color": "#1F2234",
        "shortcuts": [
            {
                "name": boltt.name + " - " + settings.lnbits_site_title,
                "short_name": boltt.name,
                "description": boltt.name + " - " + settings.lnbits_site_title,
                "url": "/boltt/" + boltt_id,
            }
        ],
    }
