# ARMlauncher
A Python based CLI tool for simplifying local deployments of [Atlassian Azure ARM templates](https://bitbucket.org/atlassian/atlassian-azure-deployment/src/master/).

## Prerequisties
> **NOTE:** Its assumed that this code will be cloned to and reside under the `./scripts` folder of the [Atlassian Azure ARM templates repo](https://bitbucket.org/atlassian/atlassian-azure-deployment/src/master/) i.e. `/atlassian-azure-deployment/src/master/scripts/`

* `Python 3`
* `pip`
* `virtualenv` or similar
* `Azure CLI`

## Installation
Login to you Azure account
```
az login
```
Create virtual environment
```
virtualenv armlaunchervenv
```
Load virtual environment
```
source armlaunchervenv/bin/activate
```
Install dependencies:
```
pip install -r requirements.txt
```

## Run
```
python main.py
```

## Customisation
The deployment parameters used by each product can be updated by modifying the `parameters` dictionary in appropriate `class` file. For example, Jira's install parameters can be updated via `./parameters/Jira.py` i.e.

```python
parameters = {
    'JiraClusterSize': "trial",
    '_artifactsLocation': self.url,
    'sshKey': self.key,
    'sshUserName': f"{self.product}admin",
    'location': self.region,
    'dbPassword': ".Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69",
    'jiraAdminUserName': "jiraadmin",
    'jiraAdminUserPassword': ".Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69",
    'enableAnalytics': False
}
```
> See [Deployment customizations](https://bitbucket.org/atlassian/atlassian-azure-deployment/src/master/HOWTO.md) for more details on how the parameters for each product can be configured. 
