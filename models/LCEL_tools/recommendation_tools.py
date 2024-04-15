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


class recommend_item_input(BaseModel):
    preferences: list[str] = Field(description="list of the flavor preferences from the user.")
    allergies: list[str] = Field(description="list of the allergies from the user.")



class Recommend_Agent_Tools:
    def __init__(self, config_path) -> None:
        self.public_tools = Public_Tools(config_path)
        self.private_tools = Private_Tools(config_path)

    def create_recommend_item_tool(self):
        recommend_item = StructuredTool.from_function(
            func=self.public_tools.recommend_item,
            name="recommend_item",
            description="Recommend a dish to the user based on user's preferences and any specified allergies.",
            args_schema=recommend_item_input,
            return_direct=False,
        )
        return recommend_item

    def create_tools(self):
        return [self.create_recommend_item_tool()]


