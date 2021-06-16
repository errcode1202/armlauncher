import re

from deployment import provision_resource_group, \
    provision_storage_account, \
    provision_storage_blob, \
    upload_assets, \
    deploy_product, \
    setup

global subscription_id, resource_group_name, product, region


def create_stack():
    setup(resource_group_name, region, product, subscription_id)
    provision_resource_group()
    provision_storage_account()
    provision_storage_blob()
    upload_assets("")
    deploy_product()


def gather_data():
    global subscription_id, resource_group_name, product, region
    subscription_id = input("Provide Azure subscription id: ")
    resource_group_name = input("Provide a name for the resource group: ")
    while True:
        product = input("Product to deploy [jira|confluence|bitbucket|crowd]: ")
        if not re.match("jira|confluence|bitbucket|crowd", product):
            print("Error! Invalid Atlassian product supplied. Please try again.")
        else:
            break
    region = input("Region to deploy to: ")


if __name__ == '__main__':
    gather_data()
    create_stack()
