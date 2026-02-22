# paypal_ynab_adapter.py
import pandas as pd
from datetime import datetime as dt
import ynab
from base import base_ynab_adapter
import string
import random

class PayPalYNABAdapter(base_ynab_adapter.BaseYNABAdapter):
    def __init__(self, api_key=None, csv_path=None, idfile="ids.txt", use_csv=False, budget_id = None, account_id = None):
        super(PayPalYNABAdapter, self).__init__(api_key=api_key, idfile=idfile, use_csv=use_csv)
        self.csv_path = csv_path
        self.transactions = None
        self.budget_id = budget_id
        self.account_id = account_id

        self.VALID_TRANSACTIONS = {
            'Handyzahlung'.strip(): 'Abgeschlossen'.strip(),
            'PayPal Express-Zahlung'.strip(): 'Abgeschlossen'.strip(),
            'Bankgutschrift auf PayPal Konto'.strip(): None,  # Any status is valid
            'Bankgutschrift auf PayPal-Konto'.strip(): None,  # Any status is valid
            'Rückzahlung'.strip(): 'Abgeschlossen'.strip(),
            'Zahlung im Einzugsverfahren mit Zahlungsrechnung'.strip(): 'Abgeschlossen'.strip(),
            'Von Nutzer eingeleitete Abbuchung'.strip(): 'Abgeschlossen'.strip(),
            'Andere'.strip(): 'Abgeschlossen'.strip(),
            'Website-Zahlung'.strip(): 'Abgeschlossen'.strip(),
            'Allgemeine Zahlung'.strip(): 'Abgeschlossen'.strip(),
        }

    def __get_transactions(self):
        try:
            data = pd.read_csv(self.csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            data = pd.read_csv(self.csv_path, encoding='iso-8859-1')

        mask = pd.Series(False, index=data.index)

        for typ, required_status in self.VALID_TRANSACTIONS.items():
            if required_status:
                mask |= (
                        (data['Typ'].str.strip() == typ) &
                        (data['Status'].str.strip() == required_status)
                )
            else:
                mask |= (data['Typ'].str.strip() == typ)

        self.transactions = data[mask]

    def create_paypal_transactions(self, from_date=None):
        if not self.account_id or not self.budget_id:
            raise ValueError("Both account_id and budget_id must be provided")

        self.__get_transactions()

        api_instance = ynab.TransactionsApi(ynab.ApiClient(self.configuration)) if not self.use_csv else None

        for _, transaction in self.transactions.iterrows():
            trans_date = dt.strptime(transaction['Datum'], '%d.%m.%Y').strftime('%Y-%m-%d')

            if from_date and trans_date < from_date:
                continue

            amount_str = str(transaction['Brutto']).replace('.', '').replace(',', '.')
            trans_amount = float(amount_str)

            memo_parts = [
                str(transaction['Typ'])[:6].strip(),
                str(transaction['Name'])[:10].strip(),
                str(transaction.get('Artikelbezeichnung', '')).strip()
            ]
            trans_memo = ' - '.join(filter(lambda x: x and x != 'nan', memo_parts))
            trans_memo = trans_memo[:200]

            trans_payee = str(transaction['Name']).strip() if pd.notna(transaction['Name']) else 'Transfer Comdirect'
            trans_payee = trans_payee[:50]

            import_id = 'PP.' + transaction['Transaktionscode']

            self._create_transaction(
                amount=trans_amount,
                memo=trans_memo,
                payee_name=trans_payee,
                trans_date=trans_date,
                account_id=self.account_id,
                api_instance=api_instance,
                import_id=import_id
            )

        if self.use_csv:
            self.intermediate_df.to_csv("paypal_ynab_upload.csv", index=False)