import json
from os import path
from comdirect import ComdirectConnector
from comdirect import comdirect_ynab_adpapter

class YNABComdirectConfig:
    def __init__(self, config_file=None):
        if not path.exists(config_file):
            raise FileNotFoundError("Config file not found")

        with open(config_file, "r") as whole_config:
            config_dict = json.load(whole_config)
            token = config_dict["ynab_api"]
            budget_id = config_dict["budget_id"]
            account_id = config_dict["account_id"]

            if path.exists(config_dict["comdirect_u_p"]):
                with open(config_dict["comdirect_u_p"]) as json_file:
                    json_dict = json.load(json_file)
                    username = json_dict['username']
                    password = json_dict['password']
            else:
                username = input('Comdirect User: ')
                password = input('Comdirect password: ')

            secret_class = ComdirectConnector.ComdirectSecrets(username=username, password=password)
            secret_class.read_client_id_secret(config_dict["comdirect_api"])
            comdirect_connector = ComdirectConnector.ComdirectConnector(secrets=secret_class)
            comdirect_connector.login()

            adapter = comdirect_ynab_adpapter.ComdirectYNABAdapter(
                api_key=token,
                comdir_connector=comdirect_connector,
                idfile=config_dict["id_file"],
                use_csv=config_dict.get("use_csv", False),
                account_id=account_id,
                budget_id=budget_id,
                # use_csv=True,
            )

            adapter.create_comdirect_transactions(
                from_date=config_dict["from_date"],
            )

if __name__ == '__main__':
    YNABComdirectConfig("C:/Users/sebas/Desktop/free/ynab_comdirect_conf.json")