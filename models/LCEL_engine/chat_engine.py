from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
import queue
import configparser
import math
import json
import asyncio
import time


class ChatEngine:
    def __init__(self, config_path) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self.model_version = self.config.get("SearchEngine", "ModelVersion")

        self.model = ChatOpenAI(model=self.model_version, temperature=0,  model_kwargs={"response_format": { "type": "json_object"}})

        