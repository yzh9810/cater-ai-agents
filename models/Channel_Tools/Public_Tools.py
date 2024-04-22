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
from search_engine import *


class Public_Tools:
    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')

        self.menu_retriever = Menu_Loading(config_path)
        self.search_engine = SearchEngine(self.menu_retriever, config_path)
        self.cart_counter = 0

        self.add_item_status_machine = {}
        self.selection_cache = {}

    def cartId_generator(self):
        self.cart_counter += 1
        return self.cart_counter
    
    def get_cache_item(self, cartId: int) -> dict:
        if cartId not in self.selection_cache:
            print(f"Error: cartId {cartId} not found in cache")
            return None
        return self.selection_cache[cartId]
    
    def add_cache_item(self, cartId, selection_info: dict) -> bool:
        print(f"add_cache_item cartId = {selection_info}")
        self.selection_cache[cartId] = {
            "status": "completed",
            "cartId": cartId,
            "item_info": {
                "item": selection_info["item_info"]["item"],
                'description': selection_info["item_info"]["description"],
                'quantity': selection_info["item_info"]["quantity"],
            },
            "selected_modifications": [],
        }
        return True
        
    def modify_cache_item(self, cartId: int, selection_info: dict) -> bool:
        # Check if cartId exists
        if cartId not in self.selection_cache:
            print(f"Error: cartId {cartId} not found in cache")
            return False
        
        # Check item name
        if self.selection_cache[cartId]["item_info"]["item"] != selection_info["item_info"]["item"]:
            print(f"Error: item name mismatch for adding item into cache, cartId = {cartId}, selection_info = {selection_info['item_info']['item']}, cache = {self.selection_cache[cartId]['item_info']['item']}")
            return False
        # Update status
        self.selection_cache[cartId]["status"] = selection_info["modifications_info"]["status"]


        # Update quantity
        self.selection_cache[cartId]["item_info"]["quantity"] = selection_info["item_info"]["quantity"]

        # Add new modifications
        for modification in selection_info["modifications_info"]["selected_modifications"]:
            if modification not in self.selection_cache[cartId]["selected_modifications"]:
                self.selection_cache[cartId]["selected_modifications"].append(modification)

        return True


    def recommend_item(self, preferences: list[str], allergies: list[str]) -> dict:
        recommended_items = self.search_engine.recommend_items_by_perference(preferences)
        return recommended_items


    def match_item(self, item: str, modifications: list[str], quantity: int) -> dict:
        item_response = self.search_engine.search_items_by_similiarity(item)
        if item_response["status"] == "selected":
            cartId = self.cartId_generator()
            item_name = item_response["option"]["name"]
            item_description = item_response["option"]["description"]

            item_info = {
                "item": item_name,
                "user_requested_item": item,
                "description": item_description,
                "quantity": quantity,
            }

            response = {
                "status": "selected",
                "cartId": cartId,
                "item_info": item_info,
            }
            print("item selected item = ", item_info["item"], " call match_modifications")
            self.add_cache_item(cartId, response)

            modifications_response = self.match_modifications(cartId, item_info["item"], modifications, item_info["quantity"])
            response = modifications_response
            

        elif item_response["status"] == "need_details":
            response = {
                "status": "need_details",
                "user_input": item,
                "options": item_response["options"],
            }
        else:
            response = {
                "status": "not_found",
                "user_input": item,
            }
        return response

    def match_modifications(self, cartId: int, item: str, modifications: list[str], quantity: int) -> dict:
        """
         {
            "status": "selected",  
            "item_info":                                // selected item details. 
                {
                    "name": item_name,
                    "user_requested_item": user_requested_item,
                    "description": item_description,
                    "quantity": quantity,
                },
            "modification_info": {                      // modification details
                    "modification_status": "completed" or "missing", 
                    "selected_modifications":               // selected modifications information.
                    [   
                        {
                            "user_requested_modification": user_requested_modification,
                            "name": modification_name,
                            "description": modification_description,	// modification description
                        }, ....
                    ],

                    "missing_modifications":               // modifications information
                    [
                        {
                            "name": modification_name,
                            "description": modification_description,
                        }, ....
                    ],

                    "unclear_modifications":               // ambiguous modifications
                    [
                        {
                            "user_requested_modification": user_requested_modification,

                            "modification_options":         // The multiple similar modifications found by system
                            [
                                {
                                    "name": option_name,
                                    "description": modification_description,
                                }, ....
                            ]
                        }
                    ],

                    "nonfound_modifications":               // Nonfound modifications
                    [
                        {
                            "user_requested_modification": user_requested_modification,
                        }
                    ],
                }
        }"""

        selected_modifications_from_user = []
        missing_modifications_from_user = []
        unclear_modifications_from_user = []
        nonfound_modifications_from_user = []

        required_modifications_from_menu = self.menu_retriever.get_modifications_by_item(item, modification_type = "Required")
        optional_modifications_from_menu = self.menu_retriever.get_modifications_by_item(item, modification_type = "Optional")

        selection_item = self.get_cache_item(cartId)
        if selection_item is None:
            print(f"Error: cartId {cartId} not found in cache")
            return None
        

        response_json = {
            "status": "selected",
            "cartId": cartId,
            "user_input": item,
            "item_info": {
                "item": selection_item["item_info"]["item"],
                "user_requested_item": selection_item["item_info"]["item"],
                "description": selection_item["item_info"]["description"],
                "quantity": selection_item["item_info"]["quantity"],
            },
        }

        for modification in modifications:
            name_response = self.search_engine.search_modification_name_by_similiarity(response_json["item_info"]["item"], modification)

            print(f"modification = {modification}, name_response = {name_response}/n")

            if name_response["status"] == "selected":
                option_name = name_response["option"]["name"]
                if option_name not in required_modifications_from_menu and option_name not in optional_modifications_from_menu:
                    print(f"Error: modification {option_name} not found in menu")

                spec_response = self.search_engine.search_modification_specs_by_similiarity(option_name, modification)
                
                print(f"modification = {modification}, spec_response = {spec_response}/n")

                if spec_response["status"] == "selected":
                    selected_modification = {
                        "user_requested_modification": modification,
                        "name": option_name,
                        "description": spec_response["option"]["name"],
                    }
                    
                    selected_modifications_from_user.append(selected_modification)

                elif spec_response["status"] == "need_details":

                    unclear_modification = {
                        "user_requested_modification": modification,
                        "modification_options": spec_response["options"],
                    }

                    unclear_modifications_from_user.append(unclear_modification)
                
                else:
                    print(f"Error: spec_response {spec_response} not found in menu")
            elif name_response["status"] == "need_details":
                unclear_modification = {
                    "user_requested_modification": modification,
                    "modification_options": name_response["options"],
                }
                unclear_modifications_from_user.append(unclear_modification)
            else:
                notfound_modification = {
                    "user_requested_modification": modification,
                }
                nonfound_modifications_from_user.append(notfound_modification)
            
        required_modifications_from_user = [modification["name"] for modification in selected_modifications_from_user if modification["name"] in required_modifications_from_menu]
        for required_modification in required_modifications_from_menu:
            if required_modification not in required_modifications_from_user:
                modification_description = self.menu_retriever.get_modification_info(required_modification)["description"]
                missing_modification = {
                    "name": required_modification,
                    "description": modification_description
                }
                missing_modifications_from_user.append(missing_modification)
        

        modification_info = {}
        if len(missing_modifications_from_user) > 0 or len(nonfound_modifications_from_user) > 0 or len(unclear_modifications_from_user) > 0:
            modification_info["status"] = "missing"
        else:
            modification_info["status"] = "completed"
        modification_info["selected_modifications"] = selected_modifications_from_user            
        modification_info["missing_modifications"] = missing_modifications_from_user
        modification_info["unclear_modifications"] = unclear_modifications_from_user
        modification_info["nonfound_modifications"] = nonfound_modifications_from_user

        response_json["modifications_info"] = modification_info

        if self.modify_cache_item(cartId, response_json) == False:
            print(f"Error: failed to modify cache item for cartId {cartId}")

        return response_json

    def add_item_cart(self, cartId: int, item: str, modifications: list[str], quantity: int) -> dict:

        selection_item = self.get_cache_item(cartId)
        if selection_item is None:
            return self.match_item(item, modifications, quantity)

        response = {
            "cartId": cartId,
            "status": selection_item["status"],
            "item_info": selection_item["item_info"],
            "selected_modifications": selection_item["selected_modifications"],
        }

        return response

    def get_resturant_info(self):
        prompt = "A boba tea shop located in the heart of the city. We offer a variety of drinks and snacks. Our business hours are from 11:00 am to 9:00 pm. We are located at 1234 Main Street, San Francisco, CA 94122. Our phone number is (415) 123-4567. We are looking forward to serving you soon!"
        return prompt