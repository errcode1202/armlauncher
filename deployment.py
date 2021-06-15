import os

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentProperties, Deployment, TemplateLink
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import PublicAccess, BlobServiceClient, AccessPolicy, ContainerSasPermissions
from datetime import datetime, timedelta
from parameters.Crowd import Crowd
from parameters.Jira import Jira
from parameters.Confluence import Confluence
from parameters.Bitbucket import Bitbucket

credential = AzureCliCredential()
azure_subscription_id = "a6864bfe-c3fd-4771-a921-616ed4c2cb0a"
storage_client = StorageManagementClient(credential, azure_subscription_id)
resource_client = ResourceManagementClient(credential, azure_subscription_id)


def provision_resource_group(resource_group_name, region):
    rg_result = resource_client.resource_groups.create_or_update(
        f"{resource_group_name}",
        {
            "location": f"{region}"
        }
    )
    print(f"Provisioned resource group {rg_result.name} in the {rg_result.location} region")


def create_storage_account(resource_group_name, region):
    storage_account_name = f"{resource_group_name}storage"
    availability_result = storage_client.storage_accounts.check_name_availability(
        {"name": storage_account_name}
    )
    if not availability_result.name_available:
        print(availability_result.message)
        print(f"Storage name {storage_account_name} is already in use. Try another name.")
        exit()

    # The name is available, so provision the account
    poller = storage_client.storage_accounts.begin_create(
        resource_group_name, storage_account_name,
        {
            "location": f"{region}",
            "kind": "StorageV2",
            "sku": {"name": "Standard_LRS"}
        }
    )

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    account_result = poller.result()
    print(f"Provisioned storage account {account_result.name}")


def create_blob(resource_group_name):
    storage_account_name = f"{resource_group_name}storage"
    blob_name = f"{storage_account_name}blob"
    container = storage_client.blob_containers.create(resource_group_name, storage_account_name, blob_name, {})
    print(f"Provisioned blob container {container.name}")


def upload(resource_group_name, product, path, dest):
    source = f"{path}/{product}"
    if os.path.isdir(source):
        print(f"Uploading templates from this location: {source}")
        upload_dir(resource_group_name, source, dest)
    else:
        print(f"Hold up! provided template location is not valid: {source}")
        exit(1)


def upload_file(resource_group_name, source, dest):
    storage_account_name = f"{resource_group_name}storage"
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"

    blob_service_client = BlobServiceClient.from_connection_string(conn_string)
    blob_name = f"{storage_account_name}blob"
    client = blob_service_client.get_container_client(blob_name)
    print(f'Uploading {source} to {dest}')
    with open(source, 'rb') as data:
        client.upload_blob(name=dest, data=data)


def upload_dir(resource_group_name, source, dest):
    prefix = '' if dest == '' else dest + '/'
    prefix += os.path.basename(source) + '/'
    for root, dirs, files in os.walk(source):
        for name in files:
            dir_part = os.path.relpath(root, source)
            dir_part = '' if dir_part == '.' else dir_part + '/'
            file_path = os.path.join(root, name)
            blob_path = prefix + dir_part + name
            upload_file(resource_group_name, file_path, blob_path)


def get_and_set_container_access_policy(resource_group_name):
    storage_account_name = f"{resource_group_name}storage"
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"
    service_client = BlobServiceClient.from_connection_string(conn_string)
    container_client = service_client.get_container_client(f"{storage_account_name}blob")

    # Create access policy
    access_policy = AccessPolicy(permission=ContainerSasPermissions(read=True, write=True),
                                 expiry=datetime.utcnow() + timedelta(hours=1),
                                 start=datetime.utcnow() - timedelta(minutes=1))

    identifiers = {'read': access_policy}

    # Specifies full public read access for container and blob data.
    public_access = PublicAccess.Container

    # Set the access policy on the container
    container_client.set_container_access_policy(signed_identifiers=identifiers, public_access=public_access)


def deploy(resource_group_name, product, region):
    get_and_set_container_access_policy(resource_group_name)
    storage_account_name = f"{resource_group_name}storage"
    blob_name = f"{storage_account_name}blob"
    template_url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/mainTemplate.json"
    url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/nestedtemplates"
    template_link = TemplateLink(uri=template_url)

    properties = DeploymentProperties(
        mode="incremental",
        template_link=template_link,
        parameters=get_parameters(product, url, region)
    )

    deploy_parameter = Deployment(properties=properties)
    deployment_async_operation = resource_client.deployments.begin_create_or_update(
        resource_group_name,
        f"{product}-deployment",
        deploy_parameter
    )
    print(f"Provisioning {product} now... Please wait.")
    deployment_async_operation.wait()
    print(f"{product} provisioning complete.")

    var = resource_client.deployments.get(
        resource_group_name,
        f"{product}-deployment").properties.outputs
    print(var)


def get_public_ssh_key():
    pub_ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    with open(pub_ssh_key_path, 'r') as pub_ssh_file_fd:
        ssh_key = pub_ssh_file_fd.read()
    return ssh_key


def get_parameters(product, url, region):
    parameters = {
        'jira': Jira(product, url, region, get_public_ssh_key()).parameters(),
        'crowd': Crowd(product, url, region, get_public_ssh_key()).parameters(),
        'confluence': Confluence(product, url, region, get_public_ssh_key()).parameters(),
        'bitbucket': Bitbucket(product, url, region, get_public_ssh_key()).parameters()
    }
    return parameters.get(product)
