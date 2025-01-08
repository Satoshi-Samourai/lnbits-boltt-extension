import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_boltt, update_boltt
from .models import CreateMyExtensionData

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


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "boltt":
        return

    boltt_id = payment.extra.get("bolttId")
    assert boltt_id, "bolttId not set in invoice"
    boltt = await get_boltt(boltt_id)
    assert boltt, "boltt does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = boltt.total - payment.amount
    else:
        total = boltt.total + payment.amount

    boltt.total = total
    await update_boltt(CreateMyExtensionData(**boltt.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<boltt_id> and then listen to it on

    some_payment_data = {
        "name": boltt.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(boltt_id, str(some_payment_data))
