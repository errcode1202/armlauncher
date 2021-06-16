import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentProperties, Deployment, TemplateLink
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import PublicAccess, BlobServiceClient, AccessPolicy, ContainerSasPermissions

from parameters.Bitbucket import Bitbucket
from parameters.Confluence import Confluence
from parameters.Crowd import Crowd
from parameters.Jira import Jira

global azure_subscription_id
global resource_group_name
global region
global product
global storage_account_name
global blob_name
global storage_client
global resource_client
global main_template_url
global nested_template_url


def setup(name, location, atlassian_product, sub_id):
    global azure_subscription_id
    azure_subscription_id = sub_id

    global resource_group_name
    resource_group_name = name

    global region
    region = location

    global product
    product = atlassian_product

    global storage_account_name
    storage_account_name = f"{resource_group_name}storage"

    global blob_name
    blob_name = f"{storage_account_name}blob"

    credential = AzureCliCredential()

    global storage_client
    storage_client = StorageManagementClient(credential, azure_subscription_id)

    global resource_client
    resource_client = ResourceManagementClient(credential, azure_subscription_id)

    global main_template_url
    main_template_url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/mainTemplate.json"

    global nested_template_url
    nested_template_url = f"https://{storage_account_name}.blob.core.windows.net/{blob_name}/{product}/nestedtemplates"


def provision_resource_group():
    resource_group = resource_client.resource_groups.create_or_update(resource_group_name, {"location": region})
    print(f"Provisioned resource group {resource_group.name} in the {resource_group.location} region")


def provision_storage_account():
    storage_account = storage_client.storage_accounts.check_name_availability({"name": storage_account_name})
    if not storage_account.name_available:
        print(storage_account.message)
        print(f"Storage name {storage_account_name} is already in use. Try another name.")
        exit()
    else:
        poller = storage_client.storage_accounts.begin_create(
            resource_group_name,
            storage_account_name,
            {
                "location": region,
                "kind": "StorageV2",
                "sku": {"name": "Standard_LRS"}
            }
        )

    account_result = poller.result()
    print(f"Provisioned storage account {account_result.name}")


def provision_storage_blob():
    blob = storage_client.blob_containers.create(resource_group_name, storage_account_name, blob_name, {})
    print(f"Provisioned blob storage {blob.name}")


def upload_assets():
    if product.__eq__("crowd"):
        print(f"Creating ansible.zip for {product}")
        os.chdir("..")
        subprocess.call(['sh', './getPlayBooks.sh'])

    source = f"{Path(__file__).resolve().parent.parent.parent}/{product}"
    if os.path.isdir(source):
        print(f"Uploading templates from this location: {source}")
        upload_dir(source)
    else:
        print(f"Hold up! provided template location is not valid: {source}")
        exit(1)


def upload_dir(source):
    prefix = os.path.basename(source) + '/'
    for root, dirs, files in os.walk(source):
        for name in files:
            dir_part = os.path.relpath(root, source)
            dir_part = '' if dir_part == '.' else dir_part + '/'
            file_path = os.path.join(root, name)
            blob_path = prefix + dir_part + name
            upload_file(file_path, blob_path)


def upload_file(source, dest):
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"

    blob_service_client = BlobServiceClient.from_connection_string(conn_string)
    client = blob_service_client.get_container_client(blob_name)
    print(f'Uploading {source} to {dest}')
    with open(source, 'rb') as data:
        client.upload_blob(name=dest, data=data)


def get_and_set_container_access_policy():
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=" \
                  f"{storage_account_name};AccountKey={keys.keys[0].value}"
    service_client = BlobServiceClient.from_connection_string(conn_string)
    container_client = service_client.get_container_client(blob_name)

    access_policy = AccessPolicy(permission=ContainerSasPermissions(read=True, write=True),
                                 expiry=datetime.utcnow() + timedelta(hours=1),
                                 start=datetime.utcnow() - timedelta(minutes=1))

    identifiers = {'read': access_policy}
    public_access = PublicAccess.Container
    container_client.set_container_access_policy(signed_identifiers=identifiers, public_access=public_access)


def deploy_product():
    get_and_set_container_access_policy()
    template_link = TemplateLink(uri=main_template_url)
    properties = DeploymentProperties(
        mode="incremental",
        template_link=template_link,
        parameters=get_parameters()
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

    deployment_details = resource_client.deployments.get(
        resource_group_name,
        f"{product}-deployment").properties.outputs
    print(deployment_details)


def get_public_ssh_key():
    pub_ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    with open(pub_ssh_key_path, 'r') as pub_ssh_file_fd:
        ssh_key = pub_ssh_file_fd.read()
    return ssh_key


def get_parameters():
    parameters = {
        'jira': Jira(product, nested_template_url, region, get_public_ssh_key()).parameters(),
        'crowd': Crowd(product, nested_template_url, region, get_public_ssh_key()).parameters(),
        'confluence': Confluence(product, nested_template_url, region, get_public_ssh_key()).parameters(),
        'bitbucket': Bitbucket(product, nested_template_url, region, get_public_ssh_key()).parameters()
    }
    return parameters.get(product)
