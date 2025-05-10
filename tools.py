from langchain_core.tools import tool
import requests
import yaml


@tool
def describe_aro_hcp_application_model() -> list:
    """
    This tool Describes the application model of ARO HCP. Use it whenever you need
    to understand the ARO HCP application model.
    This describes
    * what services and components are running on what cluster and what namespace
    * exposed endpoints
    * dependencies and interactions between services
    """
    print("  🛠️ Consulting the ARO HCP application model...")
    file_path = "rag/architecture.yaml"
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def aro_hcp_terminology() -> str:
    """Describes the ARO HCP terminology."""
    print("  🛠️ Consulting the ARO HCP terminology...")
    url = "https://raw.githubusercontent.com/Azure/ARO-HCP/refs/heads/main/docs/terminology.md"
    response = requests.get(url)
    response.raise_for_status()
    return response.text


@tool
def aro_hcp_architecture() -> str:
    """Describes the ARO HCP architecture."""
    print("  🛠️ Consulting the ARO HCP architecture documentation...")
    url = "https://raw.githubusercontent.com/Azure/ARO-HCP/refs/heads/main/docs/high-level-architecture.md"
    response = requests.get(url)
    response.raise_for_status()
    return response.text
