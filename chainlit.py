from langchain_core.tools import StructuredTool
from tools import search_and_extract_products_by_merchant, get_best_k_matching_items, get_cheapest_item

from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from langchain.schema.runnable.config import RunnableConfig

from langchain_ollama import ChatOllama

import chainlit as cl

import asyncio

async def build_graph():


    tools = [search_and_extract_products_by_merchant, get_cheapest_item]
    model = ChatOllama(model="llama3.3", temperature=0)

    llm_with_tools = model.bind_tools(tools)

    # System message
    sys_msg = SystemMessage(content="""You are a helpful assistant tasked with performing web search on merchants' websites and extract product information.
                                        please do the following:
                                        1. Search merchant's website to extract price for each of the merchants.
                                        2. compare the price by price_per_unit.
                                        3. Recommend the item with lowest price per unit""")
    
    async def assistant(state: MessagesState):
        response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])
        return {"messages": [response]}

    # Graph
    builder = StateGraph(MessagesState)

    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
    )

    builder.add_edge("tools", "assistant")
    react_graph = builder.compile()

    return react_graph
    

@cl.on_message
async def on_message(msg: cl.Message):
    config = {} #{"configurable":{"thread_id":cl.context.session.id}}
    cb = cl.LangchainCallbackHandler()

    react_graph = await build_graph()

    inputs = {"messages": [HumanMessage(content=msg.content)]}
    res = await react_graph.ainvoke(inputs, config=RunnableConfig(callbacks=[
        cl.LangchainCallbackHandler(
            stream_final_answer=True,
            to_ignore=["ChannelRead", "RunnableLambda", "ChannelWrite", "__start__", "_execute", "call_model"]

        )]))

    await cl.Message(content=res["messages"][-1].content).send()

