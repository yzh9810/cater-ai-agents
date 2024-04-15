import sys
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/Channel_Tools')

from Public_Tools import *
from Private_Tools import *
from langchain.pydantic_v1 import BaseModel, Field
from langchain.agents import create_openai_functions_agent
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor
from langchain.prompts import MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser


class match_item_input(BaseModel):
    item: str = Field(description = "The item that the user wants to add to their shopping cart.")
    modifications: list[str] = Field(description = "The modifications that the user wants to add to the item. e.g. 'large size', 'extra cheese'.")
    quantity: int = Field(description = "The number of units of the item the user intends to add to their cart. The default is 1.")

class match_modifications_input(BaseModel):
    item: str = Field(description = "The 'item' is retrieved from the response of the match_item function, located under the 'item_info' json tag.")
    modifications: list[str] = Field(description = "The modifications that the user wants to change to the item. e.g. 'large size', 'extra cheese'.")
    quantity: int = Field(description = "The number of units of the item the user intends to add to their cart. The default is 1.")



class Add_Cart_Agent_Tools:
    def __init__(self, config_path) -> None:
        self.public_tools = Public_Tools(config_path)
        self.private_tools = Private_Tools(config_path)

    def create_match_item_tool(self):
        match_item = StructuredTool.from_function(
            func=self.public_tools.match_item,
            name="match_item",
            description="Compared the items specified by the user against the existing menu items to retrieve detailed information about the product. For multiple items, call 'match_item' for each one.",
            args_schema=match_item_input,
            return_direct=False,
        )
        return match_item

    def create_match_modifications_tool(self):
        match_modifications = StructuredTool.from_function(
            func=self.public_tools.match_modifications,
            name="match_modifications",
            description="When the user is attempting to update the modifications for an already matched item, the system will call the 'match_modifications' function. This function is responsible for matching the user's requested modifications (e.g. size, ice level, or sugar level) for that specific item.",
            args_schema=match_modifications_input,
            return_direct=False,
        )
        return match_modifications

    def create_tools(self):
        return [self.create_match_item_tool(), self.create_match_modifications_tool()]