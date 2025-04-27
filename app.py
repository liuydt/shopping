from langchain_core.tools import StructuredTool
from tools import search_and_extract_products_by_merchant, get_best_k_matching_items

from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display

from langchain_ollama import ChatOllama

import asyncio

async def main():


    tools = [search_and_extract_products_by_merchant]
    model = ChatOllama(model="llama3.2", temperature=0)

    llm_with_tools = model.bind_tools(tools)

    # System message
    sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing web search on merchants' websites and extract product information.")
    
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

    messages = [HumanMessage(content="""find how much is a dozen of medium eggs from Tesco, sainsburys, ocado and ASDA, and recommend which is cheaper.  
                                        please do the following:
                                        1. Search merchant's website for price.
                                        2. compare the price by price_per_unit
                                        3. Recommend the item with lowest price per unit.""")]
    messages = await react_graph.ainvoke({"messages": messages})

    for m in messages['messages']:
        m.pretty_print()

if __name__ == "__main__":

    asyncio.run(main())
