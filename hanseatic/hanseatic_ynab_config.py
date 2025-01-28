import json
from os import path
from hanseatic import hanseatic_ynab_adpater

class YNABHanseaticConfig:
   def __init__(self, config_file=None, pdf=None):
       if not path.exists(config_file):
           raise FileNotFoundError("Config file not found")
       if not pdf or not path.exists(pdf):
           raise FileNotFoundError("Hanseatic PDF file not found")

       with open(config_file, "r") as whole_config:
           config_dict = json.load(whole_config)

           adapter = hanseatic_ynab_adpater.HanseaticYNABAdapter(
               budget_id=config_dict["budget_id"],
               account_id=config_dict["hanseatic_account_id"],
               api_key=config_dict["ynab_api"],
               idfile=path.join(path.dirname(config_file), config_dict["id_file"]),
               use_csv=config_dict.get("use_csv", False)
           )

           adapter.create_hanseatic_transactions(
               pdf_path=pdf,
               from_date=config_dict["from_date"]
           )