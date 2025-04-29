from langchain_core.tools import StructuredTool
from tools import search_and_extract_products_by_merchant, get_best_k_matching_items

from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display

from langchain_ollama import ChatOllama

import chainlit as cl

import asyncio

async def main():


    tools = [search_and_extract_products_by_merchant]
    model = ChatOllama(model="llama3.2", temperature=0)

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

    messages = [HumanMessage(content="""find how much is a dozen of medium eggs from Tesco, sainsburys, ocado and ASDA, and recommend which is cheaper.  
                                        """)]
    messages = await react_graph.ainvoke({"messages": messages})

    for m in messages['messages']:
        m.pretty_print()

if __name__ == "__main__":

    asyncio.run(main())
    

# @cl.on_message
# async def on_message(msg: cl.Message):
#     config = {"configurable":{"thread_id":cl.context.session.id}}
#     cb = cl.LangchainCallbackHandler()

#     final_answer = cl.Message(content="")

#     for msg, metadata in react_graph.stream({"message":[HumanMessage(content=msg.content)]}, 
#                                       stream_mode = "message",
#                                       config = RunnableConfig(callbacks=[cb], **config)):
#         # if ( msg.content
#         #     and not isinstance(msg, HumanMessage)):
#         await final_answer.stream_token(msg.content)

#     await final_answer.send()


# @cl.on_message
# async def on_message(msg: cl.Message):
#     #"what is the weather in sf"
#     inputs = {"messages": [HumanMessage(content=msg.content)]}

#     res = await react_graph.ainvoke(inputs, config=RunnableConfig(callbacks=[
#         cl.LangchainCallbackHandler(
#             stream_final_answer=True,
#             to_ignore=["ChannelRead", "RunnableLambda", "ChannelWrite", "__start__", "_execute", "call_model"]
#             # can add more into the to_ignore: "agent:edges", 
#             # to_keep=

#         )]))

#     await cl.Message(content=res["messages"][-1].content).send()
