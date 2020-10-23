from statistics import mode

import requests
import json
import base64
import random
import string
from PIL import Image
import tempfile


class ComdirectConnector:
    """Comdirect API connector class

    Args:
        secrets (ComdirectSecrets) An object containing all informations to connect with
        the comdirect API
    """
    def __init__(self, secrets=None):
        if type(secrets).__name__ != "ComdirectSecrets":
            exit("You must provide a ComdirectSecrets object")
        self.endpoint = "https://api.comdirect.de/"
        self.secrets = secrets
        letters = letters = string.ascii_lowercase
        self.session_id = ''.join(random.choice(letters) for i in range(12))
        self.request_id = ''.join(random.choice(letters) for i in range(10))
        self._requests = []
        self._latest_request = None
        self.access_token = None
        self.refresh_token = None
        self.session_uuid = None
        self._accounts = {}

    def login(self):
        """Run through whole oauth process

        this function goes through the whole chapter 2 of the documentation
        of the comdirect API: https://kunde.comdirect.de/cms/media/comdirect_REST_API_Dokumentation.pdf
        :return: The access token of this class will be changed to a real activation token
        """
        if self._latest_request == "oauth_secondary":
            exit("Cannot login again after full run through login procedure.")
        self.oauth_init()
        self.get_session_status()
        self.validate_session()
        self.validate_response()
        self.oath_secondary()

    def oauth_init(self):
        """run primary oauth

        POST to the comdirect API with `client_secret` and `client_id`
        :return:
        """
        self._latest_request = "oauth_init"
        self._requests.append(requests.post(url=self.endpoint + "oauth/token",
                                            data={
                                                'client_id': self.secrets.client_id,
                                                'client_secret': self.secrets.client_secret,
                                                'username': self.secrets.username,
                                                'password': self.secrets.password,
                                                'grant_type': 'password'
                                            }))
        self.access_token = self._requests[0].json()["access_token"]

    def get_session_status(self):
        """Retrieve the current session unique ID

        sets `self.session_uuid`
        :return:
        """
        if self._requests[self._requests.__len__() - 1].status_code == 200 and self._latest_request == "oauth_init":
            self._latest_request = "get_session_status"
            current_request = requests.get(
                url = self.endpoint + "api/session/clients/user/v1/sessions",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer " + self.access_token,
                    "x-http-request-info": str(
                        {'clientRequestId': {'sessionId': self.session_id, 'requestId': self.request_id}})
                })
            if current_request.status_code == 200:
                self._requests.append(current_request)
                self.session_uuid = current_request.json()[0]["identifier"]
            else:
                print(current_request.status_code)
                print(current_request.json())
                exit("Getting session status was not succesful.")
        else:
            exit("Cannot get session status without having oauth init.")

    def validate_session(self):
        """Derive a Photo TAN task from API

        This method uses the unique session ID to receive a challange to validate that
        a real person is using the AI.
        :return:
        """
        if self._latest_request == "get_session_status" and self._requests[self._requests.__len__() - 1].status_code ==\
                200:
            self._latest_request = "validate_session"
            current_request = requests.post(
                url=self.endpoint + "api/session/clients/user/v1/sessions/" + self.session_uuid + "/validate",
                json={
                    "identifier": self.session_uuid,
                    "sessionTanActive": True,
                    "activated2FA": True
                }, headers={
                    "Accept": "application/json",
                    'Content-Type': 'application/json',
                    "Authorization": "Bearer " + self.access_token,
                    "x-http-request-info": str(
                        {'clientRequestId': {'sessionId': self.session_id, 'requestId': self.request_id}})
                })
            if current_request.status_code == 201:
                self._requests.append(current_request)
            else:
                print(self._latest_request)
                print(current_request.status_code)
                print(current_request.json())

    def validate_response(self):
        """Solve the API connection challange

        This function requires user input. The function will open the PhotoTAN in
        a system program by `Pillow.Image.show()` and ask the user to
        type in the PhotoTAN received from the comdirect app.

        :return:
        """
        if self._latest_request == "validate_session" and self._requests[self._requests.__len__() - 1].status_code ==\
                201:
            self._latest_request = "validate_response"
            excerpt = json.loads(self._requests[self._requests.__len__() - 1].headers["x-once-authentication-info"])

            if excerpt['typ'] == 'P_TAN':
                tmp_image = tempfile.TemporaryFile(mode="w+b", suffix=".png")
                tmp_image.write(base64.b64decode(excerpt["challenge"]))
                img = Image.open(tmp_image)
                img.show()
                tmp_image.close()
                tan = input('Please insert the Photo TAN: ')
                current_request = requests.patch(
                    url=self.endpoint + "api/session/clients/user/v1/sessions/" + self.session_uuid,
                    json={
                        "identifier": self.session_uuid,
                        "sessionTanActive": True,
                        "activated2FA": True
                    }, headers={
                        "Accept": "application/json",
                        'Content-Type': 'application/json',
                         "Authorization": "Bearer " + self.access_token,
                        "x-http-request-info": str(
                            {'clientRequestId': {'sessionId': self.session_id, 'requestId': self.request_id}}),
                        "x-once-authentication-info": '{{\"id\": \"{tan_id}\"}}'.format(tan_id=excerpt["id"]),
                        "x-once-authentication": tan
                    })
            else:
                print("Logging in via P_TAN_PUSH, please use your phone to allow the App to access comdirect.")
                input('Press ENTER after "Freigeben"...')
                current_request = requests.patch(
                    url=self.endpoint + "api/session/clients/user/v1/sessions/" + self.session_uuid,
                    json={
                        "identifier": self.session_uuid,
                        "sessionTanActive": True,
                        "activated2FA": True
                    }, headers={
                        "Accept": "application/json",
                        'Content-Type': 'application/json',
                        "Authorization": "Bearer " + self.access_token,
                        "x-http-request-info": str(
                            {'clientRequestId': {'sessionId': self.session_id, 'requestId': self.request_id}}),
                        "x-once-authentication-info": '{{\"id\": \"{tan_id}\"}}'.format(tan_id=excerpt["id"])
                    })
            if current_request.status_code == 200:
                self._requests.append(current_request)
                print("Successfully validated TAN")
            else:
                print(self._latest_request)
                print(current_request.status_code)
                print(current_request.json())
                exit("Tan was not validated")

    def oath_secondary(self):
        """Secondary oAuth

        In case the PhotoTAN was solved successfully, this connects again with the
        API and receives the new `access_token` and the `refresh_token`

        :return:
        """
        if self._latest_request == "validate_response" and self._requests[self._requests.__len__() - 1].status_code == \
                200:
            self._latest_request = "oath_secondary"
            current_request = requests.post(
                url=self.endpoint + "oauth/token",
                data={
                    "client_id": self.secrets.client_id,
                    "client_secret":  self.secrets.client_secret,
                    "grant_type": "cd_secondary",
                    "token": self.access_token
                }, headers={
                    "Accept": "application/json",
                    'Content-Type': 'application/x-www-form-urlencoded'
                })
            if current_request.status_code == 200:
                self._requests.append(current_request)
                self.access_token = current_request.json()["access_token"]
                self.refresh_token = current_request.json()["refresh_token"]
            else:
                print(self._latest_request)
                print(current_request.status_code)
                print(current_request.json())
                exit("secondary auth failed.")

    def get_accounts(self):
        """Receive all accounts

        sets the self._accounts value to contain all accounts connected to this session

        :return:
        """
        if self._latest_request == "oath_secondary":
            r_session_accounts = requests.get(
                url=self.endpoint + "api/banking/clients/user/v1/accounts/balances",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer " + self.access_token,
                    "x-http-request-info": str({'clientRequestId': {'sessionId': self.session_id,
                                                                    'requestId': self.request_id}}),
                    'Content-Type': 'application/json'
                })
            if r_session_accounts.status_code == 200:
                print("Accounts successfully loaded")
                self._accounts = r_session_accounts.json()["values"]
        else:
            exit("Please use 'login' procedure first")

    def get_transactions(self, konto_text="Girokonto", iban=None, nr_transactions=200):
        """Receive dictionary of transactions

        this method will receive the latest transactions for an account indentified
        either by the `konto_text` or the `iban`. The `iban` will be preferred, in
        case both are given.

        :param konto_text: (str) A account name such as `Girokonto` or `Tagesgeld PLUS`
        :param iban: (str) The IBAN of the account to get transactions from
        :param nr_transactions (int): How many transcations to draw from API
        :return:
        """
        self.get_accounts()
        # Check account
        for account in self._accounts:
            if iban:
                if account["account"]["iban"] == iban:
                    current_account = account["account"]
            else:
                if account["account"]["accountType"]["text"] == konto_text:
                    current_account = account["account"]
        try:
            accountId = current_account["accountId"]
        except KeyError:
            exit("No account id was found for" + konto_text)

        # Receive transactions
        transactions_call = requests.get(
            url=self.endpoint + "api/banking/v1/accounts/{accountId}/transactions".format(accountId=accountId),
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + self.access_token,
                "x-http-request-info": str({'clientRequestId': {'sessionId': self.session_id,
                                                                'requestId': self.request_id}}),
                'Content-Type': 'application/json'
            }, params={"paging-count": int(nr_transactions)})
        # Return transaction in case it was successfull
        if transactions_call.status_code == 200:
            return transactions_call.json()["values"]
        else:
            print("Transactions could not be received")


class ComdirectSecrets:
    """Class to handle all comdirect secrets

    Args:
        username (str): Login on comdirect.de
        password (str): Password on comdirect.de
        client_id (str, optional): client_id received from comdirect API at registration
        client_secret (str, optional): client_secret received from comdirect API at registration
    """
    def __init__(self, username, password, client_id = None, client_sectret = None):
        self.password = password
        self.username = username
        self.client_id = client_id
        self.client_secret = client_sectret

    def read_client_id_secret(self, json_file):
        """setting of API credentials

        :param json_file: (str) link to a jsonfile of the following format
        {
            "client_id":"User_XXXXXX",
            "client_secret":"XXXXXXXX"
        }
        :return: setting the classes `client_id` and `client_secret`
        """
        with open(json_file) as json_file:
            data = json.load(json_file)
        self.client_id = data["client_id"]
        self.client_secret = data["client_secret"]


if __name__ == "__main__":
    # Experimental connection to API
    secret_class = ComdirectSecrets(username= "12345678", password="123456")
    secret_class.read_client_id_secret("comdirect_access.json")
    api_class = ComdirectConnector(secrets=secret_class)
    api_class.login()
    print(api_class.get_transactions())