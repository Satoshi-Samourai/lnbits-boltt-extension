# Description: Add your page endpoints here.

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from lnbits.settings import settings

from .crud import get_card, get_cards
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
        "boltt/index.html", {"request": req, "user": user.dict()}
    )


# Frontend shareable page


@boltt_generic_router.get("/{card_id}", response_class=HTMLResponse)
async def card(req: Request, card_id: str):
    card = await get_card(card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Card does not exist."
        )

    return boltt_renderer().TemplateResponse(
        "boltt/card.html",
        {
            "request": req,
            "card": card.dict(),
            "web_manifest": f"/boltt/manifest/{card_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@boltt_generic_router.get("/manifest/{card_id}.webmanifest")
async def manifest(card_id: str):
    card = await get_card(card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Card does not exist."
        )

    return {
        "short_name": f"Card {card_id}",
        "name": f"Card {card_id} - Powered by LNBITS",
        "icons": [
            {
                "src": settings.web_assets.static_url + "/card.png",
                "sizes": "192x192",
                "type": "image/png",
            }
        ],
        "start_url": f"/boltt/{card_id}",
        "background_color": "#1F2234",
        "description": "BOLTT extension for LNBITS",
        "display": "standalone",
        "theme_color": "#1F2234",
        "categories": ["finance", "card"],
        "shortcuts": [
            {
                "name": f"Card {card_id}",
                "short_name": card_id,
                "description": "View card details",
                "url": f"/boltt/{card_id}",
            }
        ],
    }
