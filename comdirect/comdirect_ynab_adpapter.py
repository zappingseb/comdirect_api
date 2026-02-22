import re
from datetime import date, datetime as dt
from base import base_ynab_adapter
import ynab
import requests
import os

class ComdirectYNABAdapter(base_ynab_adapter.BaseYNABAdapter):
    """Comdirect-specific YNAB Adapter

    Args:
        api_key (str): YNAB API KEY
        comdir_connector (ComdirectConnector): Connected Comdirect connector
        idfile (str): Path to store processed transaction IDs
        use_csv (bool): Whether to output to CSV instead of directly to YNAB
    """
    def __init__(self, api_key=None, comdir_connector=None, idfile="ids.txt",
                 use_csv=False, account_id=None, budget_id=None, amazon_csv=None):
        if not comdir_connector or type(comdir_connector).__name__ != 'ComdirectConnector':
            raise ValueError('You must provide a ComdirectConnector object')

        super().__init__(api_key=api_key, idfile=idfile, use_csv=use_csv)

        self.comdirect_connector = comdir_connector
        self.transactions = None
        self.budget_id = budget_id
        self.account_id = account_id

        # API configuration for Amazon categorizer
        self.amazon_api_url = os.getenv('AMAZON_API_URL', 'http://amazon_categorizer:5000')
        self.amazon_api_secret = os.getenv('AMAZON_API_SECRET', 'amazon_categorizer_secret_key')

    def _categorize_amazon_transaction(self, transaction_text):
        """Call the Amazon categorizer API to get category info"""
        try:
            print(f"[Amazon API] Calling categorizer with text: {transaction_text}", flush=True)
            response = requests.post(
                f'{self.amazon_api_url}/categorize',
                json={'transaction': transaction_text},
                headers={'X-API-Secret': self.amazon_api_secret},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                # The API should return a category or product name
                print(f"[Amazon API] ✓ Success (200) - Response: {data}", flush=True)
                return data
            else:
                print(f"[Amazon API] ✗ Error {response.status_code} - {response.text}", flush=True)
                return None
        except Exception as e:
            print(f"[Amazon API] ✗ Exception: {e}", flush=True)
            return None
            
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
                    category_id = None
                    
                    # Process memo
                    trans_memo = re.sub("\\s{2,20}0\\d{1}", "", transaction['remittanceInfo']).replace("01", "", 1)
                    trans_memo = (trans_memo.strip()[:177] + "...") if len(trans_memo.strip()) > 179 else trans_memo

                    # Process remitter - save full name for Amazon detection before truncation
                    if transaction["remitter"]:
                        trans_remitter_full = transaction["remitter"]["holderName"]
                        trans_remitter = (trans_remitter_full.strip()[:19]) \
                            if len(trans_remitter_full.strip()) > 19 else trans_remitter_full
                    else:
                        trans_remitter_full = re.sub("\\s{2,20}0\\d{1}", "", transaction['remittanceInfo']).replace("01", "", 1)
                        trans_remitter = trans_remitter_full[:15]

                    # Handle Amazon transactions (check full remitter name for Amazon, AMZN, or Amazon order pattern in memo)
                    is_amazon = re.search(re.compile('amazon|amzn', re.I), trans_remitter_full) or \
                               re.search(r'\d{3}-\d{7}-\d{7}', trans_memo)
                    print(f"Is Amazon: {is_amazon} and reference: {transaction['reference']}", flush=True)
                    if is_amazon:
                        # Save original memo before modification
                        trans_memo_original = trans_memo
                        # Try to categorize using the API
                        category = self._categorize_amazon_transaction(trans_memo)
                        if category:
                            # Use the order_number, category_id, category_name, and products per API response
                            order_number = category.get("order_number")
                            products = category.get("products", [])
                            category_name = category.get("category_name")
                            category_id = category.get("category_id")

                            # Memo layout: Amazon Order <order_number>: <product1>, <product2> - <category_name>
                            product_str = ", ".join(products) if products else "Unknown Product"
                            trans_memo = f"Amazon Order {order_number}: {product_str} - {category_name} - {trans_memo_original}"
                            print(f"✓ Amazon categorization SUCCESS - Order: {order_number}, Category: {category_name}, Products: {products}", flush=True)
                        else:
                            # Keep original memo if API call fails
                            trans_memo = f"Amazon: {trans_memo_original}"
                            print(f"✗ Amazon categorization FAILED - No category data returned for memo: {trans_memo_original}", flush=True)

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
                        account_id=self.account_id,
                        category_id=category_id
                    )

        if self.use_csv:
            self.intermediate_df.to_csv("comdirect_ynab_upload.csv", index=False)