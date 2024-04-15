import sys
import os

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
import json

class ManagerAgent:
    def __init__(self, config_path: str) -> None:
        # self.config = configparser.ConfigParser()
        # self.config.read(config_path)

        self.openai_api_key = "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"
        self.prompt_path = "C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/prompts/search_agent_prompts/Manger_agent.txt"
        
        with open(self.prompt_path, 'r') as file:
            self.prompt_text = file.read()

        self.model = ChatOpenAI(model="gpt-4-turbo-preview", model_kwargs={"response_format": { "type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_text),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )

        self.chat_history = []

        manger_agent_chain = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
            }
            | self.prompt
            | self.model
            | OpenAIToolsAgentOutputParser()
        )

        self.agent_executor = AgentExecutor(agent=manger_agent_chain, tools = [], verbose=True)



    def run_agent(self, user_input: str) -> dict:
        response = self.agent_executor.invoke({"input": user_input, "chat_history": self.chat_history})
        
        raw_result = response["output"]
        json_result = json.loads(response["output"])
        
        self.chat_history.extend([
            HumanMessage(content = user_input),
            AIMessage(content = raw_result)
        ])


        print("Manager Agent: ", json_result)

        return raw_result, json_result

    def clean_chat_history(self):
        self.chat_history = []

    def get_chat_history(self) -> list:
        return self.chat_history
