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
from manger_agent import *
from recommend_agent import *
from adding_cart_agent import *
import json
import time
class CaterAI:
    def __init__(self, agents: dict) -> None:
        # self.config = configparser.ConfigParser()
        # self.config.read(config_path)
        self.pending_agents = agents

        self.chat_history = []
        self.current_agent = self.pending_agents["manger_agent"]


    def run_agent(self, user_input: str) -> dict:
        start_time = time.perf_counter()

        raw_result, json_result = self.current_agent.run_agent(user_input)
        
        self.chat_history.extend([
            HumanMessage(content = user_input),
            AIMessage(content = raw_result)
        ])


        if self.handle_response(json_result):
            user_input = json_result['data']['user_message']
            raw_result, json_result = self.current_agent.run_agent(user_input)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print("elapsed_time = ", elapsed_time)
        
        return raw_result, json_result

    def run(self, user_input: str) -> str:
        raw_result, json_result = self.run_agent(user_input)
        response = json_result['data']['message']
        return response


    def get_chat_history(self) -> list:
        return self.chat_history

    def handle_response(self, agent_response: dict) -> bool:
        if agent_response["type"] == "recommend_items":
            return self.switch_to_recommend_agent()
        
        if agent_response["type"] == "add_items":
            return self.switch_to_add_items_agent()
        
        if agent_response["type"] == "exit_topic":
            return self.switch_to_manager_agent()
        return False
    
    def switch_to_recommend_agent(self):
        if "recommend_item_agent" in self.pending_agents:
            self.pending_agents["recommend_item_agent"].clean_chat_history()
            self.current_agent = self.pending_agents["recommend_item_agent"]
            return True
        
        print("Error: No recommend_item in self.pending_agents.")
        return False
    
    def switch_to_add_items_agent(self):
        if "add_items_agent" in self.pending_agents:
            self.pending_agents["add_items_agent"].clean_chat_history()
            self.current_agent = self.pending_agents["add_items_agent"]
            return True

        print("Error: No add_items_into_cart in self.pending_agents.")
        return False
    
    def switch_to_manager_agent(self):
        self.current_agent = self.pending_agents["manger_agent"]
        return True
    
