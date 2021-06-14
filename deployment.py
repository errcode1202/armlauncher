import os

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentProperties, Deployment, TemplateLink
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import PublicAccess, BlobServiceClient, AccessPolicy, ContainerSasPermissions
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


# def auth_shared_access_signature(resource_group_name):
#     storage_account_name = f"{resource_group_name}storage"
#     keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
#     conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
#                   f"{storage_account_name};AccountKey={keys.keys[0].value}"
#     blob_service_client = BlobServiceClient.from_connection_string(conn_string)
#
#     # Create a SAS token to use to authenticate a new client
#     sas_token = generate_account_sas(
#         blob_service_client.account_name,
#         account_key=blob_service_client.credential.account_key,
#         resource_types=ResourceTypes(object=True),
#         permission=AccountSasPermissions(read=True),
#         expiry=datetime.utcnow() + timedelta(hours=1)
#     )
#     return sas_token


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
    ssh_key = get_public_ssh_key()
    get_and_set_container_access_policy(resource_group_name)
    storage_account_name = f"{resource_group_name}storage"
    blob_name = f"{storage_account_name}blob"
    template_url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/mainTemplate.json"
    url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/nestedtemplates"
    template_link = TemplateLink(uri=template_url)

    parameters = {
        f'{product}ClusterSize': "trial",
        '_artifactsLocation': url,
        'sshKey': ssh_key,
        'sshUserName': f"{product}admin",
        'location': region,
        'dbPassword': ".Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69",
        'enableEmailAlerts': False,
        'enableApplicationInsights': False,
        'enableAnalytics': False
    }
    parameters = {k: {'value': v} for k, v in parameters.items()}

    properties = DeploymentProperties(
        mode="incremental",
        template_link=template_link,
        parameters=parameters
    )

    deploy_parameter = Deployment(properties=properties)
    deployment_async_operation = resource_client.deployments.begin_create_or_update(
        resource_group_name,
        f"{product}-deployment",
        deploy_parameter
    )
    print(f"Provisioning {product} now... Please wait.")
    deployment_async_operation.wait()


def get_public_ssh_key():
    pub_ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    with open(pub_ssh_key_path, 'r') as pub_ssh_file_fd:
        ssh_key = pub_ssh_file_fd.read()
    return ssh_key
