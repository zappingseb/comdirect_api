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

This package is mostly written to sync the comdirect app with your
[youneedabudget.com](https://www.youneedabudget.com/) account. The app
from the U.S.A allows managing your personal budget. I use it as there
is no European app that comes with the easiness of use and all
the features YNAB includes.

The package here presents two ways of syncing YNAB and Comdirect.

### Sync YNAB and comdirect via commandline

First you start with importing the Adapters
```python
import json
from os import path
from comdirect import ComdirectConnector

```

Afterwards the comdirect adapter needs to be prepared

```python
username = input('Comdirect User: ')
password = input('Comdirect password: ')

# Store your secrets inside a separate class
comdirect_secrets = comdirect.ComdirectConnector.ComdirectSecrets(username=username, password=password)
comdirect_secrets.read_client_id_secret('secrets.json')
# Open the comdirect connection
# It will open a PhotoTAN file that you need to solve. The TAN will be typed directly
# into the console
comdirect_connector = ComdirectConnector.ComdirectConnector(secrets=comdirect_secrets)
comdirect_connector.login()
```

To sync the last 100 transactions from the comdirect to YNAB, you need to initialize
a YNABAdapter object. Please create a `tempfile.txt` before you start. This file stores the transactions
already sent to YNAB to save your API calls not to send transactions twice.

```python
from ynabimporter import YNABAdapter
# Create a YNAB adapter
adapter = YNABAdapter.YNABAdapter(api_key="<YNAB API TOKEN>", comdir_connector=comdirect_connector,
  idfile="tempfile.txt")
# List all your budgets
adapter.get_budgets()
# Insert the ID of the budget to work in
budget_id = input('Which Budget would you like to add transactions to? [copy ID]:')
```

To sync the transactions, the YNAB adapter needs a `budget_id`. This needs to be handed over. Additionally
a `account_id` can be handed over. But if you do not define it, the tool will print all your accounts to the
command line and ask you to choose one.

Please also add a `from_date` in the format `<YYYY-MM-DD>` to filter the transactions starting at a certain date.
If no date is defined, it will just sync the transactions from today.

```python
# Sync transactions
adapter.create_comdirect_transactions(from_date='<YYYY-MM-DD>', account_id = None, budget_id = budget_id)
```

### Sync YNAB and Comdirect via config.json

You can also sync the accounts via a one line call. Therefore you need to define the following files:

- `comdirect_secrets.json`: `client_id` and `client_secret` json for comdirect API
- `comdirect_u_p.json`: JSON file containing the username and password of your comdirect account
- `config.json`: Example given below:

```json
{
  "ynab_api": "<YNAB API key as XXXXXXXXXXXX2004e413ed41ca4ef2158aedad1XXXXXXXXX>",
  "comdirect_api": "comdirect_secrets.json",
  "comdirect_u_p": "comdirect_u_p.json",
  "budget_id": "<YNAB budget ID such as XXXXXXXX-4346-4131-ac36-fc28b7082ab5>",
  "account_id": "<YNAB account ID such as XXXXXXXX-4d5b-4547-8f51-ce5f9d9a2cf5>",
  "from_date": "2020-02-20",
  "id_file": "tempfile.txt"
}
```

please adjust all file paths, the from_date, and the IDs and afterwards you can run:

```python
from ynabimporter import YNABComdirectConfig
YNABComdirectConfig.YNABComdirectConfig("config.json")
```

This will automatically ask you to solve a PhotoTAN from comdirect via the console and
if properly done, sync the desired transactions with your YNAB account.