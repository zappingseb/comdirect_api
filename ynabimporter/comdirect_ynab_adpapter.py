import re
from datetime import date, datetime as dt
import pandas as pd
from ynabimporter import base_ynab_adapter
import ynab

class ComdirectYNABAdapter(base_ynab_adapter.BaseYNABAdapter):
    """Comdirect-specific YNAB Adapter
    
    Args:
        api_key (str): YNAB API KEY
        comdir_connector (ComdirectConnector): Connected Comdirect connector
        idfile (str): Path to store processed transaction IDs
        amazon_csv (str): Optional path to Amazon order history CSV
        use_csv (bool): Whether to output to CSV instead of directly to YNAB
    """
    def __init__(self, api_key=None, comdir_connector=None, idfile="ids.txt", 
                 amazon_csv=None, use_csv=False, account_id = None, budget_id = None):
        if not comdir_connector or type(comdir_connector).__name__ != 'ComdirectConnector':
            raise ValueError('You must provide a ComdirectConnector object')
            
        super().__init__(api_key=api_key, idfile=idfile, use_csv=use_csv)
        
        self.comdirect_connector = comdir_connector
        self.transactions = None
        self.amazon_data = None
        self.budget_id = budget_id
        self.account_id = account_id

        if amazon_csv:
            self.read_amazon(amazon_csv)

    def read_amazon(self, file_name):
        """Read Amazon orders from CSV"""
        self.amazon_data = pd.read_csv(file_name)
            
    def __get_transactions(self, konto_text='Girokonto', iban=None):
        """Get transactions from Comdirect connector"""
        self.transactions = self.comdirect_connector.get_transactions(konto_text=konto_text, iban=iban)

    def create_comdirect_transactions(self, from_date=date.today().strftime('%Y-%m-%d'), konto_text='Girokonto', iban=None, paypal_account_id=None):
        """Create YNAB transactions from Comdirect data
        
        Args:
            from_date (str): Start date for transactions (YYYY-MM-DD)
            account_id (str): YNAB account ID
            budget_id (str): YNAB budget ID
            konto_text (str): Comdirect account text
            iban (str): Optional IBAN to identify account
            paypal_account_id (str): Optional PayPal account ID
        """

        # Get API instance
        api_instance = ynab.TransactionsApi(ynab.ApiClient(self.configuration)) if not self.use_csv else None
        
        # Get account ID if not provided
        if not self.account_id:
            self.get_accounts()
            account_id = input('Which account would you like to add transactions to? [copy ID]:')

        # Get transactions from Comdirect
        self.__get_transactions(konto_text=konto_text, iban=iban)
        
        for transaction in self.transactions:
            if transaction['bookingDate'] and dt.strptime(transaction['bookingDate'], '%Y-%m-%d') >= dt.strptime(
                    from_date, '%Y-%m-%d'):
                # Check date
                if dt.strptime(transaction['bookingDate'], '%Y-%m-%d') >= dt.strptime(from_date, '%Y-%m-%d'):
                    # Process transaction details
                    trans_amount = float(transaction['amount']['value'])
                    trans_date = transaction['bookingDate']
                    
                    # Process memo
                    trans_memo = re.sub("\\s{2,20}0\\d{1}", "", transaction['remittanceInfo']).replace("01", "", 1)
                    trans_memo = (trans_memo.strip()[:177] + "...") if len(trans_memo.strip()) > 179 else trans_memo

                    # Process remitter
                    if transaction["remitter"]:
                        trans_remitter = transaction["remitter"]["holderName"]
                        trans_remitter = (trans_remitter.strip()[:19]) \
                            if len(trans_remitter.strip()) > 19 else trans_remitter
                    else:
                        trans_remitter = re.sub("\\s{2,20}0\\d{1}", "", transaction['remittanceInfo']).replace("01", "", 1)[:15]

                    # Handle Amazon transactions
                    if re.match(re.compile('Amazon.*', re.I), trans_remitter):
                        if self.amazon_data is not None:
                            order_ids = re.findall('\\d{1,5}-\\d{5,9}-\\d{5,7}', trans_memo, re.DOTALL)
                            for order_id in order_ids:
                                filtered_data = self.amazon_data[self.amazon_data.order_id == order_id]
                                if filtered_data.shape[0] > 0:
                                    trans_memo = trans_memo.replace(order_id,
                                                                 re.sub("\\s", "", filtered_data.iloc[0, 1][0:45]))
                                else:
                                    print(f"The Amazon id {order_id} is not in your Export")

                    # Handle PayPal transactions
                    if re.match(re.compile('PayPal.*', re.I), trans_remitter):
                    #     trans_remitter = trans_memo.split(',', 1)[0].replace(". ", "", 1)
                        if re.match(re.compile(".*,.*"), trans_memo):
                             trans_memo = "PayPal: " + trans_memo.split(',', 1)[1]
                        else:
                             trans_memo = "PayPal:" + trans_memo

                    # Handle direct debit transactions
                    if re.match(re.compile('Lastschrift.*'), trans_remitter):
                        trans_remitter = trans_memo.split("//", 1)[0]
                        if re.match(re.compile(".*[/]{2}.*"), trans_memo):
                            trans_memo = trans_memo.split('//', 1)[1]
                        else:
                            trans_memo = "Lastschrift:" + trans_memo


                    if transaction['endToEndReference'] and transaction['endToEndReference'] == "nicht angegeben" and \
                            transaction['transactionType'] and transaction['transactionType']['key'] == "TRANSFER":
                        trans_memo = "Überweisung " + trans_memo

                    # Trim to YNAB limits
                    trans_memo = trans_memo[:200]
                    trans_remitter = trans_remitter[:50]
                    
                    # Create transaction
                    self._create_transaction(
                        amount=trans_amount,
                        memo=trans_memo,
                        payee_name=trans_remitter,
                        trans_date=trans_date,
                        cleared='cleared',
                        api_instance=api_instance,
                        import_id=transaction['reference'],
                        account_id=self.account_id
                    )

        if self.use_csv:
            self.intermediate_df.to_csv("comdirect_ynab_upload.csv", index=False)