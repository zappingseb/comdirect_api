# Comdirect API

A python package to interact with the comdirect API

# Installation

If the python package is hosted on Github, you can install directly from Github

```
pip install git+https://github.com/zappingseb/comdirect_api.git
```

Then import the package:

```python
import comdirect
```

# Usage

## Comdirect API connector

This part will explain you how to connect with the comdirect API which is documented at:

https://kunde.comdirect.de/cms/media/comdirect_REST_API_Dokumentation.pdf

### Prepare a JSON file with your comdirect API keys

Store your `client_id` and `client_secret` inside a json file called e.g. `secrets.json`

```json
{
 "client_id":"User_XXXXXXX",
 "client_secret":"XXXXXXXX"
}
```

### Use python
```python
import comdirect

username = input('Comdirect User: ')
password = input('Comdirect password: ')

# Store your secrets inside a separate class
comdirect_secrets = comdirect.ComdirectConnector.ComdirectSecrets(username=username, password=password)
comdirect_secrets.read_client_id_secret('secrets.json')

# Open the comdirect connection
# It will open a PhotoTAN file that you need to solve. The TAN will be typed directly
# into the console
comdir_con = comdirect.ComdirectConnector.ComdirectConnector(secrets=comdirect_secrets)
comdir_con.login() 

# To receive transactions for your 'Girokonto' you can call:
print(comdir_con.get_transactions())
```

## YNAB - You need a budget

```
TODO
```