from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key

from .crud import (
    create_card,
    delete_card,
    enable_disable_card,
    get_card,
    get_card_by_uid,
    get_cards,
    get_hits,
    get_refunds,
    update_card,
)
from .models import Card, CreateCardData, Hit, Refund

boltt_api_router = APIRouter()


@boltt_api_router.get("/api/v1/cards")
async def api_cards(
    key_info: WalletTypeInfo = Depends(require_invoice_key), all_wallets: bool = False
) -> list[Card]:
    wallet_ids = [key_info.wallet.id]

    if all_wallets:
        user = await get_user(key_info.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    return await get_cards(wallet_ids)


async def validate_card(data: CreateCardData):
    try:
        if len(bytes.fromhex(data.uid)) != 7:
            raise HTTPException(
                detail="Invalid bytes for card uid.", status_code=HTTPStatus.BAD_REQUEST
            )

        if len(bytes.fromhex(data.k0)) != 16:
            raise HTTPException(
                detail="Invalid bytes for k0.", status_code=HTTPStatus.BAD_REQUEST
            )

        if len(bytes.fromhex(data.k1)) != 16:
            raise HTTPException(
                detail="Invalid bytes for k1.", status_code=HTTPStatus.BAD_REQUEST
            )

        if len(bytes.fromhex(data.k2)) != 16:
            raise HTTPException(
                detail="Invalid bytes for k2.", status_code=HTTPStatus.BAD_REQUEST
            )
    except Exception as exc:
        raise HTTPException(
            detail="Invalid byte data provided.", status_code=HTTPStatus.BAD_REQUEST
        ) from exc


@boltt_api_router.put(
    "/api/v1/cards/{card_id}",
    status_code=HTTPStatus.OK,
    response_model=Card,
)
async def api_card_update(
    data: CreateCardData,
    card_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> Card:
    await validate_card(data)
    card = await get_card(card_id)
    if not card:
        raise HTTPException(
            detail="Card does not exist.", status_code=HTTPStatus.NOT_FOUND
        )
    if card.wallet != wallet.wallet.id:
        raise HTTPException(detail="Not your card.", status_code=HTTPStatus.FORBIDDEN)
    check_uid = await get_card_by_uid(data.uid)
    if check_uid and check_uid.id != card_id:
        raise HTTPException(
            detail="UID already registered. Delete registered card and try again.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    # Exclude otp from the update data
    update_data = data.dict()
    update_data.pop('otp', None)
    card = await update_card(card_id, **update_data)
    assert card, "update_card should always return a card"
    return card


@boltt_api_router.post(
    "/api/v1/cards",
    status_code=HTTPStatus.CREATED,
    response_model=Card,
)
async def api_card_create(
    data: CreateCardData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> Card:
    await validate_card(data)
    check_uid = await get_card_by_uid(data.uid)
    if check_uid:
        raise HTTPException(
            detail="Card with this UID already exists. Each card must have a unique UID.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    card = await create_card(wallet_id=wallet.wallet.id, data=data)
    assert card, "create_card should always return a card"
    return card


@boltt_api_router.get(
    "/api/v1/cards/enable/{card_id}/{enable}", status_code=HTTPStatus.OK
)
async def enable_card(
    card_id,
    enable,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    card = await get_card(card_id)
    if not card:
        raise HTTPException(detail="No card found.", status_code=HTTPStatus.NOT_FOUND)
    if card.wallet != wallet.wallet.id:
        raise HTTPException(detail="Not your card.", status_code=HTTPStatus.FORBIDDEN)
    card = await enable_disable_card(enable=enable, card_id=card_id)
    assert card
    return card.dict()


@boltt_api_router.delete("/api/v1/cards/{card_id}")
async def api_card_delete(card_id, wallet: WalletTypeInfo = Depends(require_admin_key)):
    card = await get_card(card_id)

    if not card:
        raise HTTPException(
            detail="Card does not exist.", status_code=HTTPStatus.NOT_FOUND
        )

    if card.wallet != wallet.wallet.id:
        raise HTTPException(detail="Not your card.", status_code=HTTPStatus.FORBIDDEN)

    await delete_card(card_id)
    return "", HTTPStatus.NO_CONTENT


@boltt_api_router.get("/api/v1/hits")
async def api_hits(
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[Hit]:
    wallet_ids = [key_info.wallet.id]

    if all_wallets:
        user = await get_user(key_info.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    cards = await get_cards(wallet_ids)
    cards_ids = []
    for card in cards:
        cards_ids.append(card.id)

    return await get_hits(cards_ids)


@boltt_api_router.get("/api/v1/refunds")
async def api_refunds(
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[Refund]:
    wallet_ids = [key_info.wallet.id]

    if all_wallets:
        user = await get_user(key_info.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    cards = await get_cards(wallet_ids)
    cards_ids = []
    for card in cards:
        cards_ids.append(card.id)
    hits = await get_hits(cards_ids)
    hits_ids = []
    for hit in hits:
        hits_ids.append(hit.id)

    return await get_refunds(hits_ids)