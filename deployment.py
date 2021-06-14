import json
import os

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentProperties, Deployment
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import PublicAccess, BlobServiceClient, AccessPolicy, ContainerSasPermissions, ResourceTypes, \
    AccountSasPermissions, generate_account_sas
from datetime import datetime, timedelta

credential = AzureCliCredential()
subscription_id = "???"
storage_client = StorageManagementClient(credential, subscription_id)
resource_client = ResourceManagementClient(credential, subscription_id)


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
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"
    # Step 4: Provision the blob container in the account (this call is synchronous)
    blob_name = f"{storage_account_name}blob"
    container = storage_client.blob_containers.create(resource_group_name, storage_account_name, blob_name, {})

    # The fourth argument is a required BlobContainer object, but because we don't need any
    # special values there, so we just pass empty JSON.
    print(f"Provisioned blob container {container.name}")


def upload(resource_group_name, product, dest):
    source = f"???/{product}"
    if os.path.isdir(source):
        upload_dir(resource_group_name, source, dest)
    else:
        upload_file(resource_group_name, source, dest)


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


def auth_shared_access_signature(resource_group_name):
    storage_account_name = f"{resource_group_name}storage"
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"
    blob_service_client = BlobServiceClient.from_connection_string(conn_string)

    # Create a SAS token to use to authenticate a new client
    sas_token = generate_account_sas(
        blob_service_client.account_name,
        account_key=blob_service_client.credential.account_key,
        resource_types=ResourceTypes(object=True),
        permission=AccountSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return sas_token


def deploy(resource_group_name, product):
    sas_token = auth_shared_access_signature(resource_group_name)
    storage_account_name = f"{resource_group_name}storage"
    blob_name = f"{storage_account_name}blob"
    url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/nestedtemplates"

    template_path = "???/crowd/mainTemplate.json"
    with open(template_path, 'r') as template_file_fd:
        template = json.load(template_file_fd)

    parameters = {
        'crowdClusterSize': "trial",
        '_artifactsLocation': url,
        '_artifactsLocationSasToken': f"?{sas_token}",
        'sshKey': "???",
        'sshUserName': "crowdadmin",
        'location': "northeurope",
        'dbPassword': "???",
        'enableEmailAlerts': False,
        'enableApplicationInsights': False,
        'enableAnalytics': False
    }
    parameters = {k: {'value': v} for k, v in parameters.items()}

    properties = DeploymentProperties(
        mode="incremental",
        template=template,
        parameters=parameters
    )

    deploy_parameter = Deployment(properties=properties)

    deployment_async_operation = resource_client.deployments.begin_create_or_update(
        resource_group_name,
        f"{product}-deployment",
        deploy_parameter
    )
    deployment_async_operation.wait()
