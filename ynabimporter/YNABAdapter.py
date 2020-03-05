import json
import ynab
from ynab.rest import ApiException
from comdirect import ComdirectConnector
from datetime import date
from datetime import datetime as dt
import re
from os import path


class YNABAdapter:
    """Comdirect YNAB Adapter

    Args:
        api_key (str) YNAB API KEY

        comdir_connector (ComdirectConnector) An object created that has already
        connected with the comdirect API via the `.login()` method

    Return:
        An object to move comdirect transactions over to YNAB
    """
    def __init__(self, api_key=None, comdir_connector=None):
        if type(comdir_connector).__name__ != 'ComdirectConnector':
            exit('You must provide a ComdirectConnector object')
        self.comdirect_connector = comdir_connector

        # Create a YNAB API configuration
        self.configuration = ynab.Configuration()
        self.configuration.api_key['Authorization'] = api_key
        self.configuration.api_key_prefix['Authorization'] = 'Bearer'

        self.transactions = None
        self.budget_id = None

    def __create_transaction(self, amount, memo, trans_date, account_id, api_instance, import_id, cleared='cleared'):
        """create a single transaction in YNAB

        :param amount: (float) Amount of the transaction
        :param memo: (str) memo written into YNAB
        :param trans_date: (str) date of the transaction as `YYYY-MM-DD`
        :param account_id: (str) ID of the bank account the transaction should go to
        :param api_instance: (ynab.TransactionsApi) connection
        :param import_id: (str) An importID to not import the same transaction twice
        :param cleared: (str) Whether the transaction should automatically be cleared
        :return: The output of the API /budgets/{budget_id}/transactions
            Create a single transaction or multiple transactions operation
        """
        try:
            transaction = ynab.SaveTransactionWrapper(transaction=ynab.SaveTransaction(
                account_id=account_id,
                date=trans_date,
                cleared=cleared,
                import_id=import_id,
                amount=int(round(amount * 1000)),
                memo=memo),
            )
            print(api_instance.create_transaction(self.budget_id, transaction))
        except ApiException as e:
            print('Exception when calling AccountsApi->get_account_by_id: %s\n' % e)

    def create_comdirect_transactions(self, from_date=date.today().strftime('%Y-%m-%d'), account_id=None,
                                      budget_id=None, konto_text='Girokonto',iban=None):
        """Create transactions in YNAB from Comdiret API

        :param from_date: (str, optional) Date from which to start adding transaction to YNAB (until today)
        :param account_id: (str) ID of the bank account the transaction should go to
        :param budget_id: (str) budget the account is located at
        :param konto_text: (str) Konto Text for comdirect accounts as e.g. "Girokonto"
        :param iban: (str) Alternative approach is to use the iban of the comdirect approach. If
          the iban is defined, it will be used
        :return: An output of the API /budgets/{budget_id}/transactions
            Create a single transaction or multiple transactions operation
        """
        self.budget_id = budget_id
        # Check if from_date was defined, else use today
        api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration=self.configuration))
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
                    trans_memo = transaction['remittanceInfo'].replace("01", "", 1).replace("02", "", 1).replace(
                        "03", "", 1).replace("04", "", 1)
                    trans_memo = (trans_memo.strip()[:177] + "...") if len(trans_memo.strip()) > 179 else trans_memo
                    if transaction["remitter"]:
                        trans_remitter = transaction["remitter"]["holderName"]
                        trans_remitter = (trans_remitter.strip()[:19]) \
                            if len(trans_remitter.strip()) > 19 else trans_remitter
                    else:
                        trans_remitter=''
                    trans_memo = trans_remitter + ":" + trans_memo
                    trans_cleared = 'cleared'
                    import_id = transaction['reference']
                    self.__create_transaction(amount=trans_amount, memo=trans_memo, trans_date=trans_date,
                                              account_id=account_id, cleared=trans_cleared,
                                              api_instance=api_instance, import_id = import_id)

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
    if path.exists('C:/Users/wolfs25/Desktop/comdirect_u_p.json'):
        with open('C:/Users/wolfs25/Desktop/comdirect_u_p.json') as json_file:
            json_dict = json.load(json_file)
            username = json_dict['username']
            password = json_dict['password']
    else:
        username = input('Comdirect User: ')
        password = input('Comdirect password: ')
    secret_class = ComdirectConnector.ComdirectSecrets(username=username, password=password)
    secret_class.read_client_id_secret('C:/Users/wolfs25/Desktop/comdirect_access.json')
    comdirect_connector = ComdirectConnector.ComdirectConnector(secrets=secret_class)
    comdirect_connector.login()
    transactions = comdirect_connector.get_transactions()

    with open('C:/Users/wolfs25/Desktop/ynab_token.json', 'r') as json_file:
        json_dict = json.load(json_file)
        token = json_dict['token']
        adapter = YNABAdapter(api_key=token, comdir_connector=comdirect_connector)
        adapter.get_budgets()
        budget_id = input('Which Budget would you like to add transactions to? [copy ID]:')

    adapter.create_comdirect_transactions(from_date='2020-02-20', account_id = None, budget_id = budget_id)
