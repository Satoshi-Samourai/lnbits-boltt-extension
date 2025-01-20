from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.crud import get_wallet
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

from .crud import get_card, get_hits, get_refunds

boltt_generic_router = APIRouter()


def boltt_renderer():
    return template_renderer(["boltt/boltt/templates"])


@boltt_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return boltt_renderer().TemplateResponse(
        "boltt/index.html", {"request": request, "user": user.json()}
    )


@boltt_generic_router.get("/{card_id}", response_class=HTMLResponse)
async def display(request: Request, card_id: str, user: User = Depends(check_user_exists)):
    card = await get_card(card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Card does not exist."
        )

    if card.wallet != user.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your card."
        )

    hits = await get_hits(card_id)
    refunds = [refund.hit_id for refund in await get_refunds([hit.id for hit in hits])]
    card_json = card.json(exclude={"wallet"})
    return boltt_renderer().TemplateResponse(
        "boltt/display.html",
        {
            "request": request,
            "card": card_json,
            "hits": [hit.json() for hit in hits],
            "refunds": refunds,
        },
    )