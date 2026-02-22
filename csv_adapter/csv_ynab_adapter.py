import pandas as pd
from base import base_ynab_adapter
import ynab
import hashlib

class CSVYNABAdapter(base_ynab_adapter.BaseYNABAdapter):
   def __init__(self, api_key=None, idfile="ids.txt", use_csv=False, budget_id=None, account_id=None, csv_mapping=None, csv_separator=';'):
       super(CSVYNABAdapter, self).__init__(api_key=api_key, idfile=idfile, use_csv=use_csv)
       self.budget_id = budget_id
       self.account_id = account_id
       self.csv_mapping = csv_mapping or {}
       self.csv_separator = csv_separator

   def _generate_import_id(self, row, date, amount, payee, memo):
      if 'import_id' in self.csv_mapping:
          return f"CSV.{row[self.csv_mapping['import_id']]}"
      else:
          hash_string = f"{date}{abs(amount)}{payee}{memo}"
          return f"CSV.{hashlib.md5(hash_string.encode()).hexdigest()[:12]}"

   def create_csv_transactions(self, csv_path, from_date=None):
       if not self.account_id or not self.budget_id:
           raise ValueError("Both account_id and budget_id must be provided")

       df = pd.read_csv(csv_path, sep=self.csv_separator)
       api_instance = ynab.TransactionsApi(ynab.ApiClient(self.configuration)) if not self.use_csv else None

       for _, row in df.iterrows():
           date = row[self.csv_mapping.get('date', 'Buchungstag')]
           amount = float(str(row[self.csv_mapping.get('amount', 'Betrag')]).replace(',', '.'))
           payee = row.get(self.csv_mapping.get('payee', 'Name Zahlungsbeteiligter'), '')
           memo = row.get(self.csv_mapping.get('memo', 'Verwendungszweck'), '')

           trans_date = pd.to_datetime(date, format='%d.%m.%Y').strftime('%Y-%m-%d')
           
           if from_date and trans_date < from_date:
               continue

           import_id = self._generate_import_id(row, trans_date, amount, payee, memo)

           self._create_transaction(
               amount=amount,
               memo=str(memo)[:200],
               payee_name=str(payee)[:50],
               trans_date=trans_date,
               account_id=self.account_id,
               api_instance=api_instance,
               import_id=import_id,
               cleared='cleared'
           )

       if self.use_csv:
           self.intermediate_df.to_csv("csv_ynab_upload.csv", index=False)