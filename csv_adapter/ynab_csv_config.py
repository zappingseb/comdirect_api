import json
from os import path
from csv_adapter.csv_ynab_adapter import CSVYNABAdapter

class YNABCSVConfig:
   def __init__(self, config_file=None, csv=None):
       if not path.exists(config_file):
           raise FileNotFoundError("Config file not found")
       if not csv or not path.exists(csv):
           raise FileNotFoundError("CSV file not found")

       with open(config_file, "r") as whole_config:
           config_dict = json.load(whole_config)

           adapter = CSVYNABAdapter(
               budget_id=config_dict["budget_id"],
               account_id=config_dict["csv_account_id"],
               api_key=config_dict["ynab_api"],
               idfile=path.join(path.dirname(config_file), config_dict["id_file"]),
               use_csv=config_dict.get("use_csv", False),
               csv_mapping=config_dict.get("csv_mapping", {}),
               csv_separator=config_dict.get("csv_separator", ";")
           )

           adapter.create_csv_transactions(
               csv_path=csv,
               from_date=config_dict["from_date"]
           )