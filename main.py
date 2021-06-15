# https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-example-storage?tabs=cmd#3-write-code-to-provision-storage-resources
# https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/storage/azure-storage-blob/
# https://github.com/Azure-Samples/resource-manager-python-template-deployment
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python#upload-blobs-to-a-container
# https://github.com/Azure/azure-sdk-for-python/issues/478

from deployment import provision_resource_group, create_storage_account, create_blob, upload, deploy, setup
import re


def create_stack():
    setup(resource_group_name, region, product, subscription_id)
    provision_resource_group()
    create_storage_account()
    create_blob()
    upload("")
    deploy()


if __name__ == '__main__':
    subscription_id = input("Provide Azure subscription id: ")
    resource_group_name = input("Provide a name for the resource group: ")
    while True:
        product = input("Product to deploy [jira|confluence|bitbucket|crowd]: ")
        if not re.match("jira|confluence|bitbucket|crowd", product):
            print("Error! Make sure you only use letters in your name")
        else:
            break
    region = input("Region to deploy to: ")
    create_stack()
