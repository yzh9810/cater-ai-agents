
import sys
import os
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/LCEL_tools')

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
from recommendation_tools import *
import json


class RecommendAgent:
    def __init__(self, config_path: str) -> None:
        # self.config = configparser.ConfigParser()
        # self.config.read(config_path)

        self.tools_class = Recommend_Agent_Tools(config_path)
        self.agent_tools = self.tools_class.create_tools()

        self.prompt_path = "C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/prompts/search_agent_prompts/Recommendation_agent.txt"
        
        with open(self.prompt_path, 'r') as file:
            self.prompt_text = file.read()

        self.model = ChatOpenAI(model="gpt-4-turbo-preview", model_kwargs={"response_format": { "type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_text),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),

            ]
        )

        self.chat_history = []
        self.llm_with_tools = self.model.bind_tools(self.agent_tools)

        self.agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                    x["intermediate_steps"]
                ),
                "chat_history": lambda x: x["chat_history"],
            }
            | self.prompt
            | self.llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )

        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.agent_tools, verbose=True)


    def run_agent(self, user_input: str) -> dict:
        response = self.agent_executor.invoke({"input": user_input, "chat_history": self.chat_history})
        
        raw_result = response["output"]
        json_result = json.loads(response["output"])
        
        self.chat_history.extend([
            HumanMessage(content = user_input),
            AIMessage(content = raw_result)
        ])

        print("Recommend Agent: ", json_result)
        return raw_result, json_result

    def clean_chat_history(self):
        self.chat_history = []

    def extent_chat_history(self, user_input, agent_output):
        self.chat_history.extend([
            HumanMessage(content = user_input),
            AIMessage(content = agent_output)
        ])

    def get_chat_history(self):
        return self.chat_history