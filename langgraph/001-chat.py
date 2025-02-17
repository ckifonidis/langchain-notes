

from typing import Annotated, TypedDict
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_community.tools import TavilySearchResults
from langgraph.graph.message import add_messages

tavily_tool = TavilySearchResults( max_results= 8 )
tools = [tavily_tool]

model = AzureChatOpenAI(
    deployment_name="gpt-4o-mini",
    azure_endpoint="https://biksaiservice-east-us-2.openai.azure.com/",
    api_version="2024-08-01-preview")

model_with_tools = model.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[ list, add_messages ]

def chat_node(state: ChatState) -> ChatState:
    result = model_with_tools.invoke(state["messages"])
    return { "messages": [result] }

tool_node = ToolNode(tools=tools)

def router(state: ChatState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tool_node"
    else:
        return END

graph_builder = StateGraph(ChatState)

graph_builder.add_node("chat_node", chat_node)
graph_builder.add_node("tool_node", tool_node)

graph_builder.add_edge(START, "chat_node")
graph_builder.add_conditional_edges("chat_node", router, ["tool_node", END])
graph_builder.add_edge("tool_node", "chat_node")

graph = graph_builder.compile()

image = graph.get_graph().draw_mermaid_png()

with open("001-chat.png", "wb") as f:
    f.write(image)

for chunk in graph.stream({"messages": [
        {"role": "user", "content": "What are the latest news ?"},
    ]}): 
    if "chat_node" in chunk:
        print(chunk["chat_node"]) 
    elif "tool_node" in chunk:
        print(chunk["tool_node"])
    else:
        print(chunk)
    print("---" * 50)