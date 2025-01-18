import ynab
from ynab.rest import ApiException
import pandas as pd
from os import path

class BaseYNABAdapter:
    """Base YNAB Adapter for handling YNAB connections and transactions
    
    Args:
        api_key (str): YNAB API KEY
        idfile (str): Path to store processed transaction IDs
        use_csv (bool): Whether to output to CSV instead of directly to YNAB
    """
    def __init__(self, api_key=None, idfile="ids.txt", use_csv=False, budget_id = None):
        if not api_key:
            raise ValueError("YNAB API key must be provided")
            
        # Create YNAB API configuration
        self.configuration = ynab.Configuration()
        self.configuration.api_key['Authorization'] = api_key
        self.configuration.api_key_prefix['Authorization'] = 'Bearer'
        
        self.budget_id = budget_id
        self.tempfile = idfile
        self.use_csv = use_csv
        self.ids_imported = ""
        self.intermediate_df = pd.DataFrame(columns=['import_id', 'date', 'cleared', 'amount', 'payee', 'memo'])
        
        # Read existing transaction IDs
        if path.isfile(idfile):
            self.tempfile = idfile
            with open(self.tempfile, "r") as file_object:
                self.ids_imported = file_object.read()

    def _create_transaction(self, amount, memo, payee_name, trans_date, account_id, api_instance, import_id,
                          cleared='cleared'):
        """Create a single transaction in YNAB
        
        Args:
            amount (float): Transaction amount
            memo (str): Transaction description
            payee_name (str): Name of payee
            trans_date (str): Transaction date (YYYY-MM-DD)
            account_id (str): YNAB account ID
            api_instance: YNAB API instance
            import_id (str): Unique import ID
            cleared (str): Transaction cleared status
        """
        try:
            if not self.use_csv:
                transaction = ynab.SaveTransactionWrapper(
                    transaction=ynab.SaveTransaction(
                        account_id=self.account_id,
                        date=trans_date,
                        cleared=cleared,
                        import_id=import_id,
                        amount=int(round(amount * 1000)),
                        payee_name=payee_name,
                        memo=memo
                    )
                )
            else:
                transaction = {
                    "import_id": import_id,
                    "date": trans_date,
                    "cleared": cleared,
                    "amount": amount,
                    "payee": payee_name,
                    "memo": memo
                }
                
            # Check if already imported
            already_sent = import_id in self.ids_imported if self.ids_imported else False
            
            if not already_sent:
                if self.use_csv:
                    print("Transaction saved to CSV", transaction)
                    self.intermediate_df = self.intermediate_df.append(transaction, ignore_index=True)
                else:
                    print(api_instance.create_transaction(self.budget_id, transaction))
                    
                # Record imported transaction
                with open(self.tempfile, "a") as file_object:
                    file_object.write(import_id + "\n")
            else:
                print(f"Skipping already imported transaction: {import_id}")
                
        except ApiException as e:
            print(f'Exception when creating transaction: {e}')

    def get_budgets(self):
        """Get available YNAB budgets"""
        api_instance = ynab.BudgetsApi(ynab.ApiClient(self.configuration))
        try:
            api_response = api_instance.get_budgets()
            for budget in api_response.to_dict()['data']['budgets']:
                print(f"{budget['name']}: {budget['id']}")
        except ApiException as e:
            print(f"Exception when calling BudgetsApi->get_budgets: {e}")

    def get_accounts(self):
        """Get available YNAB accounts for the current budget"""
        if not self.budget_id:
            raise ValueError("Budget ID must be set before getting accounts")
            
        api_instance = ynab.AccountsApi(ynab.ApiClient(self.configuration))
        try:
            api_response = api_instance.get_accounts(self.budget_id)
            for account in api_response.to_dict()['data']['accounts']:
                print(f"{account['name']}: {account['id']}")
        except ApiException as e:
            print(f'Exception when calling AccountsApi->get_accounts: {e}')