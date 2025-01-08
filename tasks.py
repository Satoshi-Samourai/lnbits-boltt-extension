import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_card, update_card
from .models import CreateCardData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_boltt")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do something when an invoice related to this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "boltt":
        return

    card_id = payment.extra.get("card_id")
    if not card_id:
        return

    card = await get_card(card_id)
    if not card:
        return

    # Update the websocket for the payment
    await websocket_updater(card.wallet, str(card_id))
