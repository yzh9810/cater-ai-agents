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

class SearchEngine:
    def __init__(self, menu_retriever, config_path) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')

        self.menu_retriever = menu_retriever

        self.model_version = self.config.get("SearchEngine", "ModelVersion")
        with open(self.config.get("SearchEngine", "SimilaritySearchPromptWithNonFound"), encoding='utf-8') as file:
            self.similarity_search_prompt_with_nonfound = file.read()

        with open(self.config.get("SearchEngine", "SimilaritySearchPromptMustSelect"), encoding='utf-8') as file:
            self.similarity_search_prompt_must_select = file.read()

        with open(self.config.get("SearchEngine", "SimilaritySearchCartItemsPrompt"), encoding='utf-8') as file:
            self.similarity_search_cart_items_prompt = file.read()


        self.model = ChatOpenAI(model=self.model_version, temperature=0,  model_kwargs={"response_format": { "type": "json_object"}})


    def run_similarity_search(self, prompt, user_input, options):
        prompt_template = ChatPromptTemplate.from_template(prompt)
        options = str(options)
        args = {
            "options": options,
            "input": user_input
        }

        output_parser = StrOutputParser()
        chain = prompt_template | self.model | output_parser

        response = chain.invoke(args)
        output = json.loads(response)
        return output


    async def run_similarity_search_async(self, prompt, user_input, options, thread_queue):
        prompt_template = ChatPromptTemplate.from_template(prompt)
        options = str(options)
        args = {
            "options": options,
            "input": user_input
        }

        output_parser = StrOutputParser()
        chain = prompt_template | self.model | output_parser
        response = await chain.ainvoke(args)
        output = json.loads(response)
        thread_queue.put(output)


    async def run_divide_and_conquer_async(self, prompt, user_input, options, num_each_batch = 5):
        """
        Divde and conquer the options
        
        """
        time0 = time.perf_counter()

        num_options = len(options)
        num_batches = math.ceil(num_options / num_each_batch)

        selected_options = {}

        thread_queue = queue.Queue()

        tasks = []
        for i in range(num_batches):
            start = i * num_each_batch
            end = min((i + 1) * num_each_batch, num_options)
            batch_options = options[start:end]
            tasks.append(self.run_similarity_search_async(prompt, user_input, batch_options, thread_queue))

        await asyncio.gather(*tasks)

        time1 = time.perf_counter()
        elapsed_time = time1 - time0
        print("for async elapsed_time = ", elapsed_time)

        for i in range(num_batches):
            output = thread_queue.get()
            if output["status"] == "selected":
                selected_option_name = output["option"]["name"]
                if selected_option_name != "Others":
                    selected_options[selected_option_name] = output["option"]

            elif output["status"] == "need_details":
                for option in output["options"]:
                    selected_options[option["name"]] = option

        selected_options = list(selected_options.values())

        if len(selected_options) == 0:
            return {
                "status": "not_found"
            }

        if len(selected_options) == 1:
            return {
                "status": "selected",
                "option": selected_options[0]
            }
        
        
        output = self.run_similarity_search(prompt, user_input, selected_options)
        
        time2 = time.perf_counter()
        elapsed_time = time2 - time1
        print("for sync merge time = ", elapsed_time)
        return output

    def run_divide_and_conquer(self, prompt, user_input, options, num_each_batch = 5):
        """
        Divde and conquer the options
        
        """
        time0 = time.perf_counter()

        num_options = len(options)
        num_batches = math.ceil(num_options / num_each_batch)

        selected_options = {}

        for i in range(num_batches):
            start = i * num_each_batch
            end = min((i + 1) * num_each_batch, num_options)
            batch_options = options[start:end]
            output = self.run_similarity_search(prompt, user_input, batch_options)

            if output["status"] == "selected":
                selected_option_name = output["option"]["name"]
                if selected_option_name != "Others":
                    selected_options[selected_option_name] = output["option"]

            elif output["status"] == "need_details":
                for option in output["options"]:
                    selected_options[option["name"]] = option

        selected_options = list(selected_options.values())

        time1 = time.perf_counter()
        elapsed_time = time1 - time0
        print("for non-sync elapsed_time = ", elapsed_time)

        if len(selected_options) == 0:
            return {
                "status": "not_found"
            }

        if len(selected_options) == 1:
            return {
                "status": "selected",
                "option": selected_options[0]
            }

        # print("divided options: ", selected_options)
        output = self.run_similarity_search(prompt, user_input, selected_options)

        time2 = time.perf_counter()
        elapsed_time = time2 - time1
        print("for non-sync merge time = ", elapsed_time)
        return output

    def filter_options(self, options, n_items):
        # select the top n popular items
        # options format: [{"name": item_name, "description": item_description}]
        options = sorted(options, key=lambda x: x['name'])
        return options[:n_items]


    def check_options_format(self, options):
        for option in options:
            if "name" not in option:
                print("Error: option does not have name in check_options_format")
                return False
            if "description" not in option:
                print("Error:  option does not have description in check_options_format")
                return False
        return True
    
    def check_items_format(self, items):
        for item in items:
            if "id" not in item:
                print("Error: item does not have id in check_items_format")
                return False
            
            if "name" not in item:
                print("Error: item does not have name in check_items_format")
                return False
            
            if "description" not in item:
                print("Error: item does not have description in check_items_format")
                return False
            
            if "selected_modifications" not in item:
                print("Error: item does not have selected_modifications in check_items_format")
                return False
            
            for modification in item["selected_modifications"]:
                if "modification_id" not in modification:
                    print("Error: item does not have modification_id")
                    return False
                
                if "name" not in modification:
                    print("Error: item does not have name")
                    return False
                
                if "description" not in modification:
                    print("Error: item does not have description")
                    return False
                
                if "modification_option_id" not in modification:
                    print("Error: item does not have modification_option_id")
                    return False
        return True

    def recommend_items_by_perference(self, perference_from_user, n_items = 2, items_from_menu = None):
        """
        Recommend items based on perferences

        return:
            list of item names
        """
        print("-----------------recommend_items_by_perference-----------------")
        if items_from_menu == None:
            items_from_menu = list(self.menu_retriever.get_items().keys())

        items_from_menu = [{"name": item, "description": self.menu_retriever.get_items()[item]["Description"]} for item in items_from_menu]

        # print("items_from_menu: ", items_from_menu)
        if self.check_options_format(items_from_menu) == False:
            return {
                "status": "error"
            }
        # contents = self.run_divide_and_conquer(prompt = self.similarity_search_prompt_with_nonfound, user_input = perference_from_user, options = items_from_menu, num_each_batch = 5)
        content = asyncio.run(self.run_divide_and_conquer_async(prompt = self.similarity_search_prompt_with_nonfound, user_input = perference_from_user, options = items_from_menu, num_each_batch = 5))

        if content["status"] == "need_details":
            content["options"] = self.filter_options(content["options"], n_items)
        return content

    def recommend_items_by_top_sellings(self, item_names_from_selection, num_items=2):
        """
        Recommend top selling items

        return:
            list of item names
        """

        return list(item_names_from_selection)[:num_items]


    def search_items_by_similiarity(self, item_name_from_user, n_items = 2, items_from_menu = None):
        """
        Search similar items based on item_name

        return:
            list of item names
        """
        print("-----------------search_items_by_similiarity-----------------")

        if items_from_menu == None:
            items_from_menu = [{"name": item["Name"], "description": item["Description"]} for item in self.menu_retriever.get_items().values()]

        if self.check_options_format(items_from_menu) == False:
            return {
                "status": "error"
            }
        
        content = asyncio.run(self.run_divide_and_conquer_async(prompt = self.similarity_search_prompt_with_nonfound, user_input = item_name_from_user, options = items_from_menu, num_each_batch = 5))

        if content["status"] == "need_details":
            content["options"] = self.filter_options(content["options"], n_items)
            
        return content
    
    def get_price_by_item(self, item_name, quantity, modifications):
        """
        Query price of the order with modifications

        return:
            price of the items
        """

        return
    
    
    def search_modification_name_by_similiarity(self, item_name_from_menu, modification_from_user, n_items = 2):
        """
        Search similar modifications based on modifications
        
        modifications_from_user: string of modifications

        return:
            list of modifications
        """

        print("-----------------search_modification_name_by_similiarity-----------------")

        raw_modifications = self.menu_retriever.get_modifications_by_item(item_name_from_menu)

        modifications_from_menu = []
        for modification in raw_modifications:
            modification = modification.rstrip()

            modifications_from_menu.append(
                {
                    "name": self.menu_retriever.get_modification_info(modification)["name"],
                    "description": self.menu_retriever.get_modification_info(modification)["description"]
                } )

        if self.check_options_format(modifications_from_menu) == False:
            return {
                "status": "error"
            }

        content = asyncio.run(self.run_divide_and_conquer_async(prompt = self.similarity_search_prompt_with_nonfound, user_input = modification_from_user, options = modifications_from_menu, num_each_batch = 5))

        if content["status"] == "need_details":
            content["options"] = self.filter_options(content["options"], n_items)

        return content


    def search_modification_specs_by_similiarity(self, modification_name_from_menu, modification_spec_from_user, n_items = 2):
        """
        Search similar modification spec based on modification spec

        return:
            list of modification spec
        """

        print("-----------------search_modification_specs_by_similiarity-----------------")
        modification_spec_from_menu = self.menu_retriever.get_modification_info(modification_name_from_menu)
        if modification_spec_from_menu["options"] == None:
            return {
                "status": "selected",
                "option": {
                    "name": modification_name_from_menu,
                    "description": modification_spec_from_menu
                }
            }

        modification_spec_from_menu = modification_spec_from_menu["options"]
        modification_spec_from_menu = [{"name": item["name"], "description": item["description"]} for item in modification_spec_from_menu]
        
        if self.check_options_format(modification_spec_from_menu) == False:
            return {
                "status": "error"
            }
        content = asyncio.run(self.run_divide_and_conquer_async(prompt = self.similarity_search_prompt_must_select, user_input = modification_spec_from_user, options = modification_spec_from_menu, num_each_batch = 5))
        
        if content["status"] == "need_details":
            content["options"] = self.filter_options(content["options"], n_items)

        return content


    def search_cart_items_by_similiarity(self, item_description_from_user, items_in_cart, n_items = 2):
        """
        Search similar items in cart based on item description

        return:
            list of item names
        """

        print("-----------------search_cart_items_by_similiarity-----------------")

        if self.check_items_format(items_in_cart) == False:
            return {
                "status": "error"
            }
        
        content = asyncio.run(self.run_divide_and_conquer_async(prompt = self.similarity_search_cart_items_prompt, user_input = item_description_from_user, options = items_in_cart, num_each_batch = 5))

        if content["status"] == "need_details":
            content["options"] = self.filter_options(content["options"], n_items)
        
        return content







