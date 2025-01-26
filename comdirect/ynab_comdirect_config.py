import json
import pickle
import os
from os import path
from comdirect import ComdirectConnector
from comdirect import comdirect_ynab_adpapter

class YNABComdirectConfig:
    def __init__(self, config_file=None, start_only=False, validate_only=False):
        if not path.exists(config_file):
            raise FileNotFoundError("Config file not found")

        with open(config_file, "r") as whole_config:
            self.config_dict = json.load(whole_config)
            
        connector_state_file = path.join(path.dirname(config_file), 'comdirect_state.pkl')

        if start_only:
            comdirect_up_path = path.join(path.dirname(config_file), self.config_dict["comdirect_u_p"])
            if path.exists(comdirect_up_path):
                with open(comdirect_up_path) as json_file:
                    json_dict = json.load(json_file)
                    username = json_dict['username']
                    password = json_dict['password']
            else:
                raise FileNotFoundError("Comdirect credentials file not found")

            secret_class = ComdirectConnector.ComdirectSecrets(username=username, password=password)
            comdirect_api_path = path.join(path.dirname(config_file), self.config_dict["comdirect_api"])
            secret_class.read_client_id_secret(comdirect_api_path)
            
            comdirect_connector = ComdirectConnector.ComdirectConnector(secrets=secret_class, manual_mode=False)
            comdirect_connector.oauth_init()
            comdirect_connector.get_session_status()
            comdirect_connector.validate_session()
            
            with open(connector_state_file, 'wb') as f:
                pickle.dump(comdirect_connector, f)
            return
                
        if validate_only:
            if not path.exists(connector_state_file):
                raise FileNotFoundError("No active Comdirect session found")
            
            try:
                with open(connector_state_file, 'rb') as f:
                    comdirect_connector = pickle.load(f)
                print("Loaded connector state")
            except EOFError as e:
                print(f"Error loading state: {e}")
                raise
            
            comdirect_connector.validate_response()
            comdirect_connector.oath_secondary()
            
            id_file_path = path.join(path.dirname(config_file), self.config_dict["id_file"])
            if not path.exists(id_file_path):
                raise FileNotFoundError("No ids file found.")
            
            adapter = comdirect_ynab_adpapter.ComdirectYNABAdapter(
                api_key=self.config_dict["ynab_api"],
                comdir_connector=comdirect_connector,
                idfile=id_file_path,
                use_csv=self.config_dict.get("use_csv", False),
                account_id=self.config_dict["account_id"],
                budget_id=self.config_dict["budget_id"],
            )
            
            adapter.create_comdirect_transactions(
                from_date=self.config_dict["from_date"],
            )
            
            os.remove(connector_state_file)
            return