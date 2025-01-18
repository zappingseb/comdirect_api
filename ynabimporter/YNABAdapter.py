import json
import ynab
import requests
from ynab.rest import ApiException
from comdirect import ComdirectConnector
from datetime import date
from datetime import datetime as dt
import re
from os import path
from tempfile import TemporaryFile
import pandas as pd


class YNABAdapter:
    """Comdirect YNAB Adapter

    Args:
        api_key (str) YNAB API KEY

        comdir_connector (ComdirectConnector) An object created that has already
        connected with the comdirect API via the `.login()` method

        idfile A temporary txt file where to write in IDS of transactions that were already imported

    Return:
        An object to move comdirect transactions over to YNAB
    """
    def __init__(self, api_key=None, comdir_connector=None, idfile = "C:/Users/sebas/Desktop/free/ids.txt", amazon_csv='C:/Users/sebas/Downloads/amazon_order_history (5).csv', use_csv = False):
        if type(comdir_connector).__name__ != 'ComdirectConnector':
            exit('You must provide a ComdirectConnector object')
        self.comdirect_connector = comdir_connector

        # Create a YNAB API configuration
        self.configuration = ynab.Configuration()
        self.configuration.api_key['Authorization'] = api_key
        self.configuration.api_key_prefix['Authorization'] = 'Bearer'

        self.transactions = None
        self.budget_id = None
        self.tempfile = None
        self.amazon_data = None

        self.read_amazon(amazon_csv)
        self.intermediate_df = pd.read_csv("C:/Users/sebas/Downloads/temp_ynab_upload.csv")
        self.use_csv = use_csv

        if path.isfile(idfile):
            self.tempfile = idfile
            if self.tempfile is not None:
                with open(self.tempfile, "r") as file_object :
                    self.ids_imported = file_object.read()

    def __create_transaction(self, amount, memo, payee_name, trans_date, account_id, api_instance, import_id,
                             cleared='cleared', transfer_account_id=None):
        """create a single transaction in YNAB

        :param amount: (float) Amount of the transaction
        :param memo: (str) memo written into YNAB
        :param payee_name: (str) Name of the company booking the money
        :param trans_date: (str) date of the transaction as `YYYY-MM-DD`
        :param account_id: (str) ID of the bank account the transaction should go to
        :param api_instance: (ynab.TransactionsApi) connection
        :param import_id: (str) An importID to not import the same transaction twice
        :param cleared: (str) Whether the transaction should automatically be cleared
        :param transfer_account_id : (str) If this is a transfer, insert this
        :return: The output of the API /budgets/{budget_id}/transactions
            Create a single transaction or multiple transactions operation
        """
        try:
            if not self.use_csv:

                if transfer_account_id is not None:
                    transaction = ynab.SaveTransactionWrapper(transaction=ynab.SaveTransaction(
                        account_id=account_id,
                        date=trans_date,
                        cleared=cleared,
                        import_id=import_id,
                        amount=int(round(amount * 1000)),
                        payee_name=payee_name,
                        memo=memo),
                    )
                else:
                    transaction = ynab.SaveTransactionWrapper(transaction=ynab.SaveTransaction(
                        account_id=account_id,
                        date=trans_date,
                        cleared=cleared,
                        import_id=import_id,
                        amount=int(round(amount * 1000)),
                        payee_name=payee_name,
                        memo=memo),
                    )


            else:

                transaction = {
                    "import_id":import_id,
                    "date":trans_date,
                    "cleared":cleared,
                    "amount":amount,
                    "payee":payee_name,
                    "memo":memo
                }
            already_sent = False
            # Check if the ID was already imported not too struggle too much with the YNAB API
            # because of the rate limitations
            if self.ids_imported is not None:
                if not import_id in self.ids_imported:
                    already_sent = False
                else:
                    already_sent = True
            if not already_sent:
                if self.use_csv:
                    print("Transaction saved to CSV",transaction)
                    self.intermediate_df = self.intermediate_df.append(transaction, ignore_index=True)
                else:
                    print(api_instance.create_transaction(self.budget_id, transaction))
                with open(self.tempfile, "a") as file_object:
                    file_object.write(import_id + "\n")
            else:
                print("Skippping, already imported. see tempfile: " + self.tempfile)
        except ApiException as e:
            print('Exception when calling AccountsApi->get_account_by_id: %s\n' % e)

    def read_amazon(self, file_name='C:/Users/sebas/Downloads/amazon_order_history.csv'):
        """
        Read Amazon orders from CSV
        Args:
            file_name:

        Returns:

        """
        self.amazon_data = pd.read_csv(file_name);


    def create_comdirect_transactions(self, from_date=date.today().strftime('%Y-%m-%d'), account_id=None,
                                      budget_id=None, konto_text='Girokonto',iban=None, paypal_account_id=None):
        """Create transactions in YNAB from Comdiret API

        :param from_date: (str, optional) Date from which to start adding transaction to YNAB (until today)
        :param account_id: (str) ID of the bank account the transaction should go to
        :param budget_id: (str) budget the account is located at
        :param konto_text: (str) Konto Text for comdirect accounts as e.g. "Girokonto"
        :param iban: (str) Alternative approach is to use the iban of the comdirect approach. If
          the iban is defined, it will be used
        :param paypal_account_id: (str) The id of an additional Paypal Budget if Plaid is used for sync
        :return: An output of the API /budgets/{budget_id}/transactions
            Create a single transaction or multiple transactions operation
        """
        self.budget_id = budget_id
        self.paypal_budget_id = paypal_account_id
        # Check if from_date was defined, else use today
        if not self.use_csv:
            api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration=self.configuration))
        else:
            api_instance = "xx"
        if not account_id:
            self.get_accounts()
            account_id = input('Which account would you like to add transactions to? [copy ID]:')

        # Receive transactions from comdirect account
        self.__get_transactions(konto_text=konto_text,iban=iban)
        for transaction in self.transactions:
            if transaction['bookingDate']:
                if dt.strptime(transaction['bookingDate'], '%Y-%m-%d') >= dt.strptime(from_date, '%Y-%m-%d'):
                    trans_amount = float(transaction['amount']['value'])
                    trans_date = transaction['bookingDate']
                    trans_memo = re.sub("\\s{2,20}0\\d{1}", "", transaction['remittanceInfo']).replace("01", "", 1)
                    trans_memo = (trans_memo.strip()[:177] + "...") if len(trans_memo.strip()) > 179 else trans_memo
                    if transaction["remitter"]:
                        trans_remitter = transaction["remitter"]["holderName"]
                        trans_remitter = (trans_remitter.strip()[:19]) \
                            if len(trans_remitter.strip()) > 19 else trans_remitter
                    else:
                        trans_remitter=''

                    if re.match(re.compile('Amazon.*', re.I), trans_remitter):
                        print("Checking out amazon order")
                        if self.amazon_data is not None:
                            order_ids = re.findall('\\d{1,5}-\\d{5,9}-\\d{5,7}', trans_memo, re.DOTALL)
                            for order_id in order_ids:
                                filtered_data = self.amazon_data[self.amazon_data.order_id == order_id]
                                if (filtered_data.shape[0] > 0):
                                    trans_memo = trans_memo.replace(order_id, re.sub("\\s", "", filtered_data.iloc[0, 1][0:45]))
                                else:
                                    print("The Amazon id ", order_id, " is not in your Export")

                    create_paypal = False
                    if re.match(re.compile('PayPal.*', re.I), trans_remitter):
                        trans_remitter = trans_memo.split(',', 1)[0].replace(". ","", 1)
                        if re.match(re.compile(".*,.*"), trans_memo):
                            trans_memo = "PayPal: " + trans_memo.split(',', 1)[1]
                        else:
                            trans_memo = "PayPal:" + trans_memo
                        create_paypal = True

                    if re.match(re.compile('Lastschrift.*'), trans_remitter):
                        trans_remitter = trans_memo.split("//", 1)[0]
                        if re.match(re.compile(".*[/]{2}.*"), trans_memo):
                            trans_memo = trans_memo.split('//', 1)[1]
                        else:
                            trans_memo = "Lastschrift:" + trans_memo
                    trans_memo = trans_memo[0:199]
                    trans_remitter = trans_remitter[0:49]
                    trans_cleared = 'cleared'
                    import_id = transaction['reference']


                    self.__create_transaction(amount=trans_amount, memo=trans_memo, payee_name=trans_remitter,
                                              trans_date=trans_date,
                                              account_id=account_id, cleared=trans_cleared,
                                              api_instance=api_instance, import_id = import_id)

        self.intermediate_df.to_csv("C:/Users/sebas/Downloads/temp_ynab_upload.csv")

    def __get_transactions(self, konto_text='Girokonto', iban=None):
        self.transactions = self.comdirect_connector.get_transactions(konto_text=konto_text, iban=iban)

    def get_accounts(self):
        """Receive account Name and ID from YNAB

        :return: None, only printed to console
        """
        api_instance = ynab.AccountsApi(ynab.ApiClient(self.configuration))
        try:
            # Account list
            api_response = api_instance.get_accounts(self.budget_id)
            for account in api_response.to_dict()['data']['accounts']:
                print(account['name'] + ': ' + account['id'])
        except ApiException as e:
            print('Exception when calling AccountsApi->get_accounts: %s\n' % e)

    def get_budgets(self):
        """Receive budgets from YNAB

        :return: None, only printed to console
        """
        api_instance = ynab.BudgetsApi(ynab.ApiClient(self.configuration))
        try:
            # List budgets
            api_response = api_instance.get_budgets()
            for budget in api_response.to_dict()['data']['budgets']:
                print(budget['name'] + ': ' + budget['id'])
        except ApiException as e:
            print("Exception when calling BudgetsApi->get_budgets: %s\n" % e)


if __name__ == '__main__':
    if path.exists('C:/Users/sebas/Desktop/free/comdirect_u_p.json'):
        with open('C:/Users/sebas/Desktop/free/comdirect_u_p.json') as json_file:
            json_dict = json.load(json_file)
            username = json_dict['username']
            password = json_dict['password']
    else:
        username = input('Comdirect User: ')
        password = input('Comdirect password: ')
    secret_class = ComdirectConnector.ComdirectSecrets(username=username, password=password)
    secret_class.read_client_id_secret('C:/Users/sebas/Desktop/free/comdirect_access.json')
    comdirect_connector = ComdirectConnector.ComdirectConnector(secrets=secret_class)
    comdirect_connector.login()
    transactions = comdirect_connector.get_transactions()

    with open('C:/Users/sebas/Desktop/free/ynab_token.json', 'r') as json_file:
        json_dict = json.load(json_file)
        token = json_dict['token']
        adapter = YNABAdapter(api_key=token, comdir_connector=comdirect_connector)
        adapter.get_budgets()
        budget_id = input('Which Budget would you like to add transactions to? [copy ID]:')

    adapter.create_comdirect_transactions(from_date='2020-02-20', account_id = None, budget_id = budget_id)
