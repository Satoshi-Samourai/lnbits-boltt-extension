# Description: This file contains the extensions API endpoints.

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException

from .crud import (
    create_boltt,
    delete_boltt,
    get_boltt,
    get_boltts,
    update_boltt,
)
from .helpers import lnurler
from .models import CreateMyExtensionData, CreatePayment, boltt

boltt_api_router = APIRouter()

# Note: we add the lnurl params to returns so the links
# are generated in the boltt model in models.py

## Get all the records belonging to the user


@boltt_api_router.get("/api/v1/myex")
async def api_boltts(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    wallet: WalletTypeInfo = Depends(require_invoice_key),
) -> list[boltt]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    wallet_ids = user.wallet_ids if user else []
    boltts = await get_boltts(wallet_ids)

    # Populate lnurlpay and lnurlwithdraw for each instance.
    # Without the lnurl stuff this wouldnt be needed.
    for myex in boltts:
        myex.lnurlpay = lnurler(myex.id, "boltt.api_lnurl_pay", req)
        myex.lnurlwithdraw = lnurler(myex.id, "boltt.api_lnurl_withdraw", req)

    return boltts


## Get a single record


@boltt_api_router.get(
    "/api/v1/myex/{boltt_id}",
    dependencies=[Depends(require_invoice_key)],
)
async def api_boltt(boltt_id: str, req: Request) -> boltt:
    myex = await get_boltt(boltt_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )
    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "boltt.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "boltt.api_lnurl_withdraw", req)

    return myex


## Create a new record


@boltt_api_router.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_boltt_create(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateMyExtensionData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> boltt:
    myex = await create_boltt(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Withoutthe lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "boltt.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "boltt.api_lnurl_withdraw", req)

    return myex


## update a record


@boltt_api_router.put("/api/v1/myex/{boltt_id}")
async def api_boltt_update(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateMyExtensionData,
    boltt_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> boltt:
    myex = await get_boltt(boltt_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )

    if wallet.wallet.id != myex.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your boltt."
        )

    for key, value in data.dict().items():
        setattr(myex, key, value)

    myex = await update_boltt(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "boltt.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "boltt.api_lnurl_withdraw", req)

    return myex


## Delete a record


@boltt_api_router.delete("/api/v1/myex/{boltt_id}")
async def api_boltt_delete(
    boltt_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    myex = await get_boltt(boltt_id)

    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )

    if myex.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your boltt."
        )

    await delete_boltt(boltt_id)
    return


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@boltt_api_router.post("/api/v1/myex/payment", status_code=HTTPStatus.CREATED)
async def api_boltt_create_invoice(data: CreatePayment) -> dict:
    boltt = await get_boltt(data.boltt_id)

    if not boltt:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="boltt does not exist."
        )

    # we create a payment and add some tags,
    # so tasks.py can grab the payment once its paid

    payment = await create_invoice(
        wallet_id=boltt.wallet,
        amount=data.amount,
        memo=(
            f"{data.memo} to {boltt.name}" if data.memo else f"{boltt.name}"
        ),
        extra={
            "tag": "boltt",
            "amount": data.amount,
        },
    )

    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}
