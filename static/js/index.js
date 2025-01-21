const mapCards = obj => {
  obj.date = Quasar.date.formatDate(new Date(obj.time), 'YYYY-MM-DD HH:mm')
  return obj
}

window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  data() {
    return {
      toggleAdvanced: false,
      disableNfcButton: true,
      lnurlLink: `${window.location.host}/boltt/api/v1/scan/`,
      cards: [],
      hits: [],
      refunds: [],
      cardDialog: {
        show: false,
        data: {
          wallet: '',
          card_name: '',
          uid: null,
          counter: 0,
          verification_limit: 0,
          daily_limit: 0,
          enable: true
        },
        temp: {}
      },
      appQrDialog: {
        show: false,
        link: 'https://github.com/Satoshi-Samourai/boltcard-verifier-cap/releases/latest/download/BOLTT-App.apk'
      },
      cardsTable: {
        columns: [
          {
            name: 'card_name',
            align: 'left',
            label: 'Card name',
            field: 'card_name'
          },
          {
            name: 'counter',
            align: 'left',
            label: 'Counter',
            field: 'counter'
          },
          {
            name: 'wallet',
            align: 'left',
            label: 'Wallet',
            field: 'wallet'
          },
          {
            name: 'verification_limit',
            align: 'left',
            label: 'Verification Limit',
            field: 'verification_limit'
          },
          {
            name: 'daily_limit',
            align: 'left',
            label: 'Daily Limit',
            field: 'daily_limit'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      refundsTable: {
        columns: [
          {
            name: 'hit_id',
            align: 'left',
            label: 'Hit ID',
            field: 'hit_id'
          },
          {
            name: 'refund_amount',
            align: 'left',
            label: 'Refund Amount',
            field: 'refund_amount'
          },
          {
            name: 'date',
            align: 'left',
            label: 'Time',
            field: 'date'
          }
        ],
        pagination: {
          rowsPerPage: 10,
          sortBy: 'date',
          descending: true
        }
      },
      hitsTable: {
        columns: [
          {
            name: 'card_name',
            align: 'left',
            label: 'Card name',
            field: 'card_name'
          },
          {
            name: 'amount',
            align: 'left',
            label: 'Amount',
            field: 'amount'
          },
          {
            name: 'old_ctr',
            align: 'left',
            label: 'Old counter',
            field: 'old_ctr'
          },
          {
            name: 'new_ctr',
            align: 'left',
            label: 'New counter',
            field: 'new_ctr'
          },
          {
            name: 'date',
            align: 'left',
            label: 'Time',
            field: 'date'
          },
          {
            name: 'ip',
            align: 'left',
            label: 'IP',
            field: 'ip'
          },
          {
            name: 'useragent',
            align: 'left',
            label: 'User agent',
            field: 'useragent'
          }
        ],
        pagination: {
          rowsPerPage: 10,
          sortBy: 'date',
          descending: true
        }
      },
      qrCodeDialog: {
        show: false,
        wipe: false,
        data: null
      }
    }
  },
  computed: {
  },
  watch: {
    'cardDialog.data.verification_limit': function(newVal) {
      if (newVal > this.cardDialog.data.daily_limit) {
        this.$q.notify({
          type: 'warning',
          message: 'Verification limit cannot be higher than daily limit',
          timeout: 5000
        })
        // Reset to daily limit if it's higher
        this.cardDialog.data.verification_limit = this.cardDialog.data.daily_limit
      }
    },
    'cardDialog.data.daily_limit': function(newVal) {
      // If verification limit is higher than new daily limit, adjust it down
      if (this.cardDialog.data.verification_limit > newVal) {
        this.cardDialog.data.verification_limit = newVal
      }
    }
  },
  methods: {
    readNfcTag() {
      const ndef = new NDEFReader()
      const readerAbortController = new AbortController()
      readerAbortController.signal.onabort = event => {
        console.log('All NFC Read operations have been aborted.')
      }

      Quasar.Notify.create({
        message: 'Tap your NFC tag to copy its UID here.'
      })

      return ndef.scan({signal: readerAbortController.signal}).then(() => {
        ndef.onreadingerror = () => {
          this.disableNfcButton = false
          Quasar.Notify.create({
            type: 'negative',
            message: 'There was an error reading this NFC tag.'
          })
          readerAbortController.abort()
        }

        ndef.onreading = ({message, serialNumber}) => {
          const uid = serialNumber.toUpperCase().replaceAll(':', '')
          //Decode NDEF data from tag
          this.cardDialog.data.uid = uid
          Quasar.Notify.create({
            type: 'positive',
            message: 'NFC tag read successfully.'
          })
        }
      })
    },
    getCards() {
      LNbits.api
        .request(
          'GET',
          '/boltt/api/v1/cards?all_wallets=true',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.cards = response.data.map(function (obj) {
            return mapCards(obj)
          })
        })
        .then(() => {
          this.getHits()
        })
    },
    getHits() {
      LNbits.api
        .request(
          'GET',
          '/boltt/api/v1/hits?all_wallets=true',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.hits = response.data.map(obj => {
            obj.card_name = this.cards.find(d => d.id == obj.card_id).card_name
            return mapCards(obj)
          })
        })
    },
    getRefunds() {
      LNbits.api
        .request(
          'GET',
          '/boltt/api/v1/refunds?all_wallets=true',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.refunds = response.data.map(obj => {
            return mapCards(obj)
          })
        })
    },
    openQrCodeDialog(cardId, wipe) {
      var card = _.findWhere(this.cards, {id: cardId})
      this.qrCodeDialog.data = {
        id: card.id,
        link: window.location.origin + '/boltt/api/v1/auth?a=' + card.otp,
        name: card.card_name,
        uid: card.uid,
        external_id: card.external_id
      }
      this.qrCodeDialog.wipe = wipe
      this.qrCodeDialog.show = true
    },
    openAppQrDialog() {
      console.log('Opening app QR dialog with link:', this.appQrDialog.link)  
      this.appQrDialog.show = true
    },
    addCardOpen() {
      this.cardDialog.show = true
    },
    closeFormDialog() {
      this.cardDialog.data = {}
    },
    sendFormData() {
      const wallet = this.g.user.wallets[0]
      const data = this.cardDialog.data

      if (this.cardDialog.temp?.id) {
        this.updateCard(wallet, data)
      } else {
        this.createCard(wallet, data)
      }
    },
    createCard(wallet, data) {
      LNbits.api
        .request('POST', '/boltt/api/v1/cards', wallet.adminkey, data)
        .then(response => {
          this.cards.push(mapCards(response.data))
          this.cardDialog.show = false
          this.cardDialog.data = {}
        })
        .catch(LNbits.utils.notifyApiError)
    },
    updateCardDialog(formId) {
      var card = _.findWhere(this.cards, {id: formId})
      // Find the wallet that owns this card
      const cardWallet = this.g.user.wallets.find(w => w.id === card.wallet)
      if (!cardWallet) {
        this.$q.notify({
          type: 'negative',
          message: 'Card belongs to a different wallet',
          timeout: 5000
        })
        return
      }
      this.cardDialog.temp = {id: formId, wallet: cardWallet}
      this.cardDialog.data = _.clone(card)

      this.cardDialog.show = true
    },
    updateCard(wallet, data) {
      const cardId = this.cardDialog.temp.id
      const cardWallet = this.cardDialog.temp.wallet
      LNbits.api
        .request(
          'PUT',
          '/boltt/api/v1/cards/' + cardId,
          cardWallet.adminkey,  // Use the correct wallet's admin key
          data
        )
        .then(response => {
          this.cards = _.reject(this.cards, obj => obj.id === cardId)
          this.cards.push(mapCards(response.data))
          this.cardDialog.show = false
          this.cardDialog.data = {}
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    enableCard(wallet, card_id, enable) {
      let fullWallet = _.findWhere(this.g.user.wallets, {
        id: wallet
      })
      LNbits.api
        .request(
          'GET',
          '/boltt/api/v1/cards/enable/' + card_id + '/' + enable,
          fullWallet.adminkey
        )
        .then(response => {
          console.log(response.data)
          this.cards = _.reject(this.cards, function (obj) {
            return obj.id == response.data.id
          })
          this.cards.push(mapCards(response.data))
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    deleteCard(cardId) {
      let cards = _.findWhere(this.cards, {id: cardId})

      LNbits.utils
        .confirmDialog(
          "Are you sure you want to delete this card? Without access to the card keys you won't be able to reset them in the future!"
        )
        .onOk(() => {
          LNbits.api
            .request(
              'DELETE',
              '/boltt/api/v1/cards/' + cardId,
              _.findWhere(this.g.user.wallets, {id: cards.wallet}).adminkey
            )
            .then(response => {
              this.cards = _.reject(this.cards, function (obj) {
                return obj.id == cardId
              })
            })
            .catch(function (error) {
              LNbits.utils.notifyApiError(error)
            })
        })
    },
    exportCardsCSV() {
      LNbits.utils.exportCSV(this.cardsTable.columns, this.cards)
    },
    exportHitsCSV() {
      LNbits.utils.exportCSV(this.hitsTable.columns, this.hits)
    },
    exportRefundsCSV() {
      LNbits.utils.exportCSV(this.refundsTable.columns, this.refunds)
    },
    copyText(text) {
      // Ensure text is a string and not undefined
      if (!text) {
        console.error('No text provided to copy')
        this.$q.notify({
          message: 'Nothing to copy',
          color: 'red'
        })
        return
      }
      
      console.log('Attempting to copy:', text)
      
      // Use a more robust clipboard API approach
      if (navigator.clipboard && window.isSecureContext) {
        // For modern browsers
        navigator.clipboard.writeText(text)
          .then(() => {
            console.log('Successfully copied using Clipboard API')
            this.$q.notify({
              message: 'Copied to clipboard!',
              color: 'green'
            })
          })
          .catch(err => {
            console.error('Clipboard API failed:', err)
            // Fall back to older method
            this.fallbackCopyText(text)
          })
      } else {
        // Fall back to older method
        this.fallbackCopyText(text)
      }
    },
    
    fallbackCopyText(text) {
      try {
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        
        const successful = document.execCommand('copy')
        document.body.removeChild(textArea)
        
        if (successful) {
          console.log('Successfully copied using fallback method')
          this.$q.notify({
            message: 'Copied to clipboard!',
            color: 'green'
          })
        } else {
          throw new Error('Copy command failed')
        }
      } catch (err) {
        console.error('Fallback copy failed:', err)
        this.$q.notify({
          message: 'Failed to copy to clipboard',
          color: 'red'
        })
      }
    }
  },
  created() {
    if (this.g.user.wallets.length) {
      this.getCards()
      this.getRefunds()
    }
    try {
      if (typeof NDEFReader == 'undefined') {
        throw {
          toString() {
            return 'NFC not supported on this device or browser.'
          }
        }
      }
      this.disableNfcButton = false
      Quasar.Notify.create({
        type: 'positive',
        message: 'NFC is supported on this device. You can now read NFC tags.'
      })
    } catch (error) {
      Quasar.Notify.create({
        type: 'negative',
        message: error ? error.toString() : 'An unexpected error has occurred.'
      })
    }
  }
})