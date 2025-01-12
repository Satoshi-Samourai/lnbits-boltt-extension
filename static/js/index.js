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
          k0: null,
          k1: null,
          k2: null,
          counter: 0,
          daily_limit: null,
          limit1: null,
          limit2: null,
          pin: null,
          confirmPin: null
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
            name: 'tx_limit',
            align: 'left',
            label: 'Max tx',
            field: 'tx_limit'
          },
          {
            name: 'daily_limit',
            align: 'left',
            label: 'Daily tx limit',
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
    showPinFields() {
      const limit1 = parseInt(this.cardDialog.data.limit1) || 0;
      const limit2 = parseInt(this.cardDialog.data.limit2) || 0;
      return limit2 > 0 && (limit1 === 0 || limit2 > limit1);
    }
  },
  watch: {
    'cardDialog.data.limit2': function(newVal) {
      const limit1 = parseInt(this.cardDialog.data.limit1) || 0;
      const limit2 = parseInt(newVal) || 0;
      
      // Clear PINs if Limit2 is cleared or less than/equal to Limit1 (when Limit1 is set)
      if (limit2 === 0 || (limit1 > 0 && limit2 <= limit1)) {
        this.cardDialog.data.pin = null;
        this.cardDialog.data.confirmPin = null;
      }
    },
    'cardDialog.data.limit1': function(newVal) {
      const limit1 = parseInt(newVal) || 0;
      const limit2 = parseInt(this.cardDialog.data.limit2) || 0;
      
      // Clear PINs if Limit1 is set and greater than or equal to Limit2
      if (limit1 > 0 && limit2 > 0 && limit2 <= limit1) {
        this.cardDialog.data.pin = null;
        this.cardDialog.data.confirmPin = null;
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
        external_id: card.external_id,
        k0: card.k0,
        k1: card.k1,
        k2: card.k2,
        k3: card.k1,
        k4: card.k2
      }
      this.qrCodeDialog.data_wipe = JSON.stringify({
        action: 'wipe',
        k0: card.k0,
        k1: card.k1,
        k2: card.k2,
        k3: card.k1,
        k4: card.k2,
        uid: card.uid,
        version: 1
      })
      this.qrCodeDialog.wipe = wipe
      this.qrCodeDialog.show = true
    },
    openAppQrDialog() {
      console.log('Opening app QR dialog with link:', this.appQrDialog.link)  
      this.appQrDialog.show = true
    },
    addCardOpen() {
      this.cardDialog.show = true
      this.generateKeys()
    },
    generateKeys() {
      const genRandomHexBytes = size =>
        crypto
          .getRandomValues(new Uint8Array(size))
          .reduce((acc, i) => acc + i.toString(16).padStart(2, '0'), '')

      debugcard =
        typeof this.cardDialog.data.card_name === 'string' &&
        this.cardDialog.data.card_name.search('debug') > -1

      this.cardDialog.data.k0 = debugcard
        ? '11111111111111111111111111111111'
        : genRandomHexBytes(16)

      this.cardDialog.data.k1 = debugcard
        ? '22222222222222222222222222222222'
        : genRandomHexBytes(16)

      this.cardDialog.data.k2 = debugcard
        ? '33333333333333333333333333333333'
        : genRandomHexBytes(16)
    },
    closeFormDialog() {
      this.cardDialog.data = {}
    },
    sendFormData() {
      let wallet = _.findWhere(this.g.user.wallets, {
        id: this.cardDialog.data.wallet
      })
      let data = this.cardDialog.data
      if (data.id) {
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
      this.cardDialog.data = _.clone(card)

      this.cardDialog.temp.k0 = this.cardDialog.data.k0
      this.cardDialog.temp.k1 = this.cardDialog.data.k1
      this.cardDialog.temp.k2 = this.cardDialog.data.k2

      this.cardDialog.show = true
    },
    updateCard(wallet, data) {
      if (
        this.cardDialog.temp.k0 != data.k0 ||
        this.cardDialog.temp.k1 != data.k1 ||
        this.cardDialog.temp.k2 != data.k2
      ) {
        data.prev_k0 = this.cardDialog.temp.k0
        data.prev_k1 = this.cardDialog.temp.k1
        data.prev_k2 = this.cardDialog.temp.k2
      }

      LNbits.api
        .request(
          'PUT',
          '/boltt/api/v1/cards/' + data.id,
          wallet.adminkey,
          data
        )
        .then(response => {
          this.cards = _.reject(this.cards, function (obj) {
            return obj.id == data.id
          })
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

      Quasar.exportFile(
        cards.card_name + '.json',
        this.qrCodeDialog.data_wipe,
        'application/json'
      )

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