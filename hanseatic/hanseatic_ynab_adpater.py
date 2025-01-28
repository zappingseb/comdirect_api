import pdfplumber
from datetime import datetime
import re
from base import base_ynab_adapter
import ynab
import hashlib

class HanseaticYNABAdapter(base_ynab_adapter.BaseYNABAdapter):
   def __init__(self, api_key=None, idfile="ids.txt", use_csv=False, budget_id=None, account_id=None):
       super(HanseaticYNABAdapter, self).__init__(api_key=api_key, idfile=idfile, use_csv=use_csv)
       self.budget_id = budget_id
       self.account_id = account_id

   def _generate_import_id(self, date, amount):
      hash_string = f"{date}{abs(amount)}"
      hash_object = hashlib.md5(hash_string.encode())
      return f"HB.{hash_object.hexdigest()[:12]}"

   def parse_hanseatic_statement(self, pdf_path):
       transactions = []
       with pdfplumber.open(pdf_path) as pdf:
           for page in pdf.pages:
               text = page.extract_text()
               lines = text.split('\n')
               current_date = None
               
               for i, line in enumerate(lines):
                   date_match = re.match(r'(\d{2}\.\d{2}\.\d{4})', line)
                   if date_match:
                       current_date = datetime.strptime(date_match.group(1), '%d.%m.%Y').strftime('%Y-%m-%d')
                       
                       amount_match = re.search(r'(-?\d+,\d{2})', line)
                       if amount_match:
                           amount = float(amount_match.group(1).replace(',', '.'))
                           description = ' '.join(line.split())
                           payee = lines[i + 1]
                           if description.find("Neuer Saldo") == -1 and description.find("vereinbart") == -1:
                               transactions.append({
                                   'date': current_date,
                                   'description': description,
                                   'amount': amount,
                                   'payee': payee.split()[0] if "Kartenabrechnung" in payee else payee
                               })
                   
                   elif current_date and re.search(r'(-?\d+,\d{2})', line):
                       amount_match = re.search(r'(-?\d+,\d{2})', line)
                       amount = float(amount_match.group(1).replace(',', '.'))
                       description = ' '.join(line.split())
                       payee = lines[i + 1]
                       if description.find("Neuer Saldo") == -1 and description.find("vereinbart") == -1:
                           transactions.append({
                               'date': current_date,
                               'description': description,
                               'amount': amount,
                               'payee': payee.split()[0] if "Kartenabrechnung" in payee else payee
                           })
               
       return transactions

   def create_hanseatic_transactions(self, pdf_path, from_date=None):
       if not self.account_id or not self.budget_id:
           raise ValueError("Both account_id and budget_id must be provided")

       transactions = self.parse_hanseatic_statement(pdf_path)
       print(transactions, flush=True)
       api_instance = ynab.TransactionsApi(ynab.ApiClient(self.configuration)) if not self.use_csv else None

       for transaction in transactions:
           if from_date and transaction['date'] < from_date:
               print("Transaction lower from date", transaction['import_id'], flush=True)
               continue

           import_id = self._generate_import_id(date=transaction['date'], amount=transaction['amount'])

           self._create_transaction(
               amount=transaction['amount'],  # Convert to milliunits
               memo=transaction['description'][:200],
               payee_name=transaction['payee'][:50],
               trans_date=transaction['date'],
               account_id=self.account_id,
               api_instance=api_instance,
               import_id=import_id
           )

       if self.use_csv:
           self.intermediate_df.to_csv("hanseatic_ynab_upload.csv", index=False)
