# https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-example-storage?tabs=cmd#3-write-code-to-provision-storage-resources
# https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/storage/azure-storage-blob/
# https://github.com/Azure-Samples/resource-manager-python-template-deployment
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python#upload-blobs-to-a-container
# https://github.com/Azure/azure-sdk-for-python/issues/478

from deployment import provision_resource_group, create_storage_account, create_blob, upload, deploy


def create_stack():
    provision_resource_group(resource_group_name, region)
    create_storage_account(resource_group_name, region)
    create_blob(resource_group_name)
    upload(resource_group_name, product, "")
    deploy(resource_group_name, product, region)


if __name__ == '__main__':
    resource_group_name = input("Provide a name for the resource group: ")
    product = input("Product to deploy: ")
    region = input("Region to deploy to: ")
    create_stack()
