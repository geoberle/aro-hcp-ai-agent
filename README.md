# ARO HCP AI Agent

This is an experimental day-of-learning project that aims to create an AI agent capable of helping SREs managing ARO HCP. The goal is to provide a tool that can assist in various tasks related to ARO HCP, such as troubleshooting or simply navigating the platform.

## Involved technologies

* langchain and langgraph for the AI agent
* various LLMs capable of reasoning and tool usage, such as IBM Granite 3.3 8B instruct or OpenAI o4-mini
* Googles [kubectl-ai](https://github.com/GoogleCloudPlatform/kubectl-ai) in MCP mode for Kubernetes tool usage

## Disclamer

⚠️ Don't use this with an environment that contains sensitive data. This is an experimental project and should not be used in production environments. The AI agent will (!) make mistakes or provide incorrect information. Use at your own risk.

## Example Usage

```shell
uv venv
uv run agent.py

🔧 ARO HCP Chat Agent
👤 You: in what namespace is CS running?
  🛠️ Consulting the ARO HCP application model...
🤖 Agent: The Clusters Service (CS) is deployed in the Kubernetes namespace `cluster-service`.
👤 You: check the health of CS
  🛠️ kubectl get pods -n cluster-service
  🛠️ kubectl describe pod clusters-service-946d7498f-lk4xp -n cluster-service
  🛠️ kubectl logs clusters-service-946d7498f-lk4xp -n cluster-service -c service --tail 100
  🛠️ kubectl logs clusters-service-946d7498f-lk4xp -n cluster-service -c service --previous --tail 100
  🛠️ kubectl exec -n cluster-service clusters-service-79cbd9568f-9b68n -c service -- sh -c "curl -s -o /dev/null -w '%{http_code}' http://localhost:8083/healthcheck"
🤖 Agent: The Clusters Service (CS) pod set shows one healthy pod and one that’s failing to start:

• clusters-service-79cbd9568f-9b68n – Running and healthy
• clusters-service-946d7498f-lk4xp – Failed (preempted)

Health check on the running pod (79cbd9568f-9b68n) returned HTTP 200 on the `/healthcheck` endpoint, so CS is healthy overall. The failure on the second pod is due to Kubernetes preemption; you can safely leave it to the ReplicaSet to spin up a replacement. If it consistently fails, you may want to review cluster resource quotas or node taints/priorities.
```
