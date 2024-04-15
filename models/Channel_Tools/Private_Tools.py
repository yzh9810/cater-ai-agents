import sys
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/LCEL_engine/')
sys.path.append('C:/Users/yuezo/OneDrive/桌面/project/cater-ai-agents/models/Menu_Retriever/')

import os
import json
import time
import sys
import configparser
from openai import OpenAI
from langchain.tools import tool
from menu_retriever import *


class Private_Tools:
    def __init__(self, user_id):
        self.user_id = user_id

        self.cart_items = {}
        self.suggested_items = {}

        self.pending_order = {}

    def add_item_into_cart(self, item: str, modifications: list[str], quantity: int):
        pass


    def remove_item_from_cart(self, item_name):
        pass

