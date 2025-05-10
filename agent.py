import os

from typing import Literal
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ChatMessage, ToolCall
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from tools import describe_aro_hcp_application_model, aro_hcp_terminology, aro_hcp_architecture
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.client import StdioConnection
from pprint import pprint

from langchain.callbacks.base import BaseCallbackHandler

class PrintThinkingHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(token, end="", flush=True)

def log_tool_call(tool_call: ToolCall):
    if tool_call["name"] == "kubectl":
        print(f"  🛠️ {tool_call['args']['command']}")

async def start_agent(tools: list) -> None:
    llm = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        #temperature=0,
        openai_api_base=os.environ["OPENAI_API_BASE"],
        api_key=os.environ.get("OPENAI_API_KEY"),
    ).bind_tools(tools)

    # llm = ChatOllama(
    #     model=os.environ["MODEL_NAME"],
    #     callbacks=[PrintThinkingHandler()],
    # ).bind_tools(tools)

    def expert(state: MessagesState) -> str:
        system_message = """
            You are a helpful AI assistent that answers questions about ARO HCP and helps debugging issues on AKS cluters and Azure infrastructure.

            About the tools you can use:
            * If you don't know a term, you can use the aro_hcp_terminology tool to fetch the ARO HCP terminology. Don't halucinate what abbreviations stand for!!!
            * The available services, their deployment and dependencies are describe in the ARO HCP application model. You can use the describe_aro_hcp_application_model tool to fetch it.
            * When using the kubectl tool, avoid fetching too much data, e.g. restrict pod logs to the last 100 lines.
              The kubectl tool requires a command and modifies_resources yes/no arg. Don't forget them.

            Don't be hesistant to use these tools.

            Don't run any unapproved workloads on the clusters.

            Do not make things up. If you don't know the answer, say "I don't know"!
        """
        messages = state["messages"]
        response = llm.invoke([system_message] + messages)
        response = llm.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    def should_expert_use_tools(state: MessagesState) -> Literal["tools", END]:
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            for tc in last_message.tool_calls:
                log_tool_call(tc)
            return "tools"
        return END


    graph = StateGraph(MessagesState)

    graph.add_node("expert", expert)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "expert")
    graph.add_conditional_edges("expert", should_expert_use_tools)
    graph.add_edge("tools", "expert")

    checkpointer = MemorySaver()

    agent = graph.compile(checkpointer=checkpointer)


    class LanggraphAgentInterface:

        agent: CompiledStateGraph

        def __init__(self, agent: CompiledStateGraph):
            self.agent = agent

        async def send_message(self, query: str) -> str:
            messages :list[ChatMessage] = []
            if "granite3.3" in os.environ["MODEL_NAME"]:
               messages.append(
                   # https://github.com/langchain-ai/langchain/pull/30411/files
                   ChatMessage(role="control", content="thinking"),
               )
            messages.append(ChatMessage(role="user", content=query))
            response = await self.agent.ainvoke(
                {"messages": messages},
                config={
                    "configurable": {
                        "thread_id": 1,
                    }
                },
            )
            content = response["messages"][-1].content
            return content

    agent_interface = LanggraphAgentInterface(agent)
    print("🔧 ARO HCP Chat Agent")
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        result = await agent_interface.send_message(user_input)
        print(f"🤖 Agent: {result}")


async def main():
    async with MultiServerMCPClient(
        {
            "kubernetes": StdioConnection(
                transport="stdio",
                env={
                    "OPENAI_ENDPOINT": os.environ["OPENAI_API_BASE"],
                    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
                },
                command="kubectl-ai",
                args=["--mcp-server","--llm-provider","openai","--model","granite-3-8b-instruct","--kubeconfig",os.environ["KUBECONFIG"]]
            )
        }
    ) as mcp_client:
        tools = mcp_client.get_tools()
        tools.append(describe_aro_hcp_application_model)
        tools.append(aro_hcp_terminology)
        tools.append(aro_hcp_architecture)
        await start_agent(tools)

if __name__ == "__main__":
    asyncio.run(main())
