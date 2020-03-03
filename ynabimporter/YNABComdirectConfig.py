import json
from os import path
from comdirect import ComdirectConnector
from ynabimporter import YNABAdapter


class YNABComdirectConfig:
    """Copying comdirect transactions to YNAB with single config json

    Args:
        config_file (str) path to a json file with the following content

        ```
        {
          "ynab_api": "<YNAB API TOKEN>",
          "comdirect_api": "<LINK TO FILE WITH COMDIRECT API CLIENT ID AND SECRET>",
          "comdirect_u_p": "<LINK TO FILE WITH COMDIRET USERNAME AND PASSWORD (optional)>",
          "budget_id": "<YNAB BUDGET ID as XXXXXXXX-4346-4131-ac36-fc28b7082ab5>",
          "account_id": "<YNAB ACCOUNT ID AS XXXXXXXX-4d5b-4547-8f51-ce5f9d9a2cf5>",
          "from_date": "<DATE FROM WHICH TO START TAKING TRANSACTIONS AS YYYY-MM-DD>"
        }
        ```

    Returns:
        This tool will try to start a connection to the comdirect API. Therefore
        it will ask for validating a photo TAN. You must type into the command line
        which TAN was requested.

        Afterwards it automatically commits all transactions after the chosen
        date to the YNAB API. Transactions cannot be duplicated as the reference
        key from comdirect is used for each submission.
    """
    def __init__(self, config_file=None):
        if not path.exists(config_file):
            exit("config file not found")
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
            adapter = YNABAdapter.YNABAdapter(api_key=token, budget_id=budget_id,
                                              comdir_connector=comdirect_connector)
            adapter.create_comdirect_transactions(from_date=config_dict["from_date"], account_id=account_id)


if __name__ == '__main__':
    YNABComdirectConfig("C:/Users/wolfs25/Desktop/ynab_comdirect_conf.json")