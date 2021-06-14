# https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-example-storage?tabs=cmd#3-write-code-to-provision-storage-resources
# https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/storage/azure-storage-blob/
# https://github.com/Azure-Samples/resource-manager-python-template-deployment
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python#upload-blobs-to-a-container

from deployment import provision_resource_group, create_storage_account, create_blob, upload, deploy


def create_stack(name, location):
    provision_resource_group(name, location)
    create_storage_account(name, location)
    create_blob(name)
    upload(name, product, "")
    deploy(name, product)


if __name__ == '__main__':
    # Capture details
    resource_group_name = input("Provide a name for the resource group: ")
    region = input("Region to deploy to: ")
    product = input("Product to deploy: ")
    create_stack(resource_group_name, region)
