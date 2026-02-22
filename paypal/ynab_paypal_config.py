import json
from os import path
from paypal import paypal_ynab_adapter

class YNABPayPalConfig:
    def __init__(self, config_file=None, csv=None):
        if not path.exists(config_file):
            raise FileNotFoundError("Config file not found")
        if not csv or not path.exists(csv):
            raise FileNotFoundError("PayPal CSV file not found")

        with open(config_file, "r") as whole_config:
            config_dict = json.load(whole_config)

            adapter = paypal_ynab_adapter.PayPalYNABAdapter(
                budget_id=config_dict["budget_id"],
                account_id=config_dict["paypal_account_id"],
                api_key=config_dict["ynab_api"],
                csv_path=csv,
                idfile=path.join(path.dirname(config_file), config_dict["id_file"]),
                use_csv=config_dict.get("use_csv", False)
            )

            adapter.create_paypal_transactions(
                from_date=config_dict["from_date"]
            )

if __name__ == '__main__':
    YNABPayPalConfig(
        "C:/Users/sebas/Desktop/free/ynab_comdirect_conf.json",
        csv="C:/Users/sebas/Downloads/Download(7).csv"
    )