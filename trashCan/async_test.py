import sys
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/LCEL_engine/')
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/Menu_Retriever/')

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from menu_retriever import *
import time

import asyncio
import configparser
import math
import json
import os


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls__e33af7b422394942b1ca565215fd1b92"
os.environ["OPENAI_API_KEY"] = "sk-proj-AlzmJmyqlP3OQ0J8C72BT3BlbkFJRGzI1k47rj0QDWF790U7"

async def async_search(prompt, user_input, options):
    prompt_template = ChatPromptTemplate.from_template(prompt)
    options = str(options)
    # print("input = ", user_input)
    # print("options = ", options)
    args = {
        "options": options,
        "input": user_input
    }

    output_parser = StrOutputParser()
    chain = prompt_template | model | output_parser

    response = await chain.ainvoke(args)
    print("response = ", response)
    return response

def sync_search(prompt, user_input, options):
    prompt_template = ChatPromptTemplate.from_template(prompt)
    options = str(options)
    # print("input = ", user_input)
    # print("options = ", options)
    args = {
        "options": options,
        "input": user_input
    }

    output_parser = StrOutputParser()
    chain = prompt_template | model | output_parser

    response = chain.invoke(args)
    print("response = ", response)
    return response

model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0,  model_kwargs={"response_format": { "type": "json_object"}})
menu_retriever = Menu_Loading("C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/scripts/example.cfg")
with open("C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/prompts/seach_engine_prompts/similarity_search_with_nonfound.txt") as file:
    prompt = file.read()

items_from_menu = list(menu_retriever.get_items().keys())

options = [{"name": item, "description": menu_retriever.get_items()[item]["Description"]} for item in items_from_menu]
user_input = "boba milk tea"

num_each_batch = 5
num_options = len(options)
num_batches = math.ceil(num_options / num_each_batch)

async def run_tasks():
    tasks = []
    for i in range(num_batches):
        start = i * num_each_batch
        end = min((i + 1) * num_each_batch, num_options)
        batch_options = options[start:end]
        tasks.append(async_search(prompt, user_input, batch_options))
    result = await asyncio.gather(*tasks)
    return result

def sync_run_tasks():
    tasks = []
    for i in range(num_batches):
        start = i * num_each_batch
        end = min((i + 1) * num_each_batch, num_options)
        batch_options = options[start:end]
        sync_search(prompt, user_input, batch_options)
    result = tasks
    return result

start_time = time.perf_counter()
results = asyncio.run(run_tasks())
# sync_run_tasks()
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print("elapsed_time = ", elapsed_time)



