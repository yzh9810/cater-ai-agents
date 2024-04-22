import json
import configparser

class Menu_Loading:
    def __init__(self, config_path) -> None:
        """
        Load menu and modification description from json files
        items_info: get all items info
        custom_info: get all modifications info
        category_info: get all category info
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')

        # path to menu json file
        self.menu_path = self.config.get('Menu_Loading', 'MenuPath')                                      
        
        # path to modification description file
        self.custom_desc_path = self.config.get('Menu_Loading', 'CustomDescPath')    

        # path to item description file
        self.item_desc_path = self.config.get('Menu_Loading', 'ItemDescPath')         
        
        self.item_desc = self.load_item_desc()

        # dict of item information: 
            # {
            #     key: item_name, 
            #     value: item information
            # }  
        self.items_info = self.load_menu()
        
        # dict of category to item names:
            # {
            #     key: category_name, 
            #     value: list of item names
            # }
        self.custom_desc = self.load_custom_desc()
        
        # dict of category to item names:
            # {
            #     key: category_name,
            #     value: list of item names
            # }
        self.items_by_category = self.load_category() 
        
        # dict of modification spec:
            # {
            #     key: modification_name,
            #     value: {"name", "description", "values"}
            # }
        self.custom_info = self.load_modification()

        # dict of id to item name mapping
            # {
            #     key: item_id,
            #     value: item_name
            # }
        self.id_to_item_name = {v["ID"]: v["Name"] for k, v in self.items_info.items()}
        

        # dict of item name to id mapping
            # {
            #     key: item_name,
            #     value: item_id
            # }
        self.item_name_to_id = {v["Name"]: v["ID"] for k, v in self.items_info.items()}
        
        

        # dict of category to category description
        self.category_info = [
                {
                    "name": "Milk Tea",
                    "description": "Classic milk tea with toppings."
                },
                {
                    "name": "Teaspresso",
                    "description": "Concentrated tea shots."
                },
                {
                    "name": "Jelly Tea",
                    "description": "Tea with jelly."
                },
                {
                    "name": "Fruit Tea",
                    "description": "Tea with fruit flavors."
                },
                {
                    "name": "Sea Salt Tea",
                    "description": "Tea with sea salt foam."
                },
                {
                    "name": "Frosty Blends",
                    "description": "Fruit and tea smoothies."
                },
                {
                    "name": "Hot Drinks",
                    "description": "Warm beverages."
                },
                {
                    "name": "Milk & Sago",
                    "description": "Milk tea with sago."
                },
                {
                    "name": "Snacks",
                    "description": "Quick bites."
                },
                {
                    "name": "Meals",
                    "description": "Noodles and rice."
                }
            ]

    def load_custom_desc(self):

        with open(self.custom_desc_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        description_dict = {}
        for line in lines:
            name, description = line.replace('\n', '').split(': ')
            description_dict[name] = description
        
        return description_dict

    def load_item_desc(self):
            
        with open(self.item_desc_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        description_dict = {}
        for line in lines:
            name, description = line.replace('\n', '').split(': ')
            description_dict[name] = description
        
        return description_dict


    def load_menu(self):
        """
        Load menu from menu_path

        return: 
            dict of menu items:
                key: item name
                value: item information
        """

        with open(self.menu_path, 'r', encoding='utf-8') as f:
            menu = json.load(f)
        
        menu_dict = {}
        for raw_item in menu:
            # print(raw_item['name'])
            item_name = raw_item['name']['en-US'].rstrip()
            if item_name == 'I4 Golden Ovaltine Malt Drink.':
                item_name = 'I4 Golden Ovaltine Malt Drink'

            if item_name == "D12 Strawberry":
                item_name = 'D12 Strawberry Fruit Tea'

            menu_item = {
                "ID": raw_item["_id"]["$oid"],
                "Name": item_name,
                "Category": raw_item["categoryRef"]["name"]["en-US"],
                "modifications": {
                    "Required": [],
                    "Optional": []
                }
            }

            for specification in raw_item['specifications']:
                if specification["name"]["en-US"] == "Modifications":
                    continue
                
                modification_name = specification["name"]["en-US"]
                modification_name = modification_name.rstrip(' ')

                if "required" not in specification:
                    menu_item["modifications"]["Required"].append(modification_name)

                elif specification["required"] == True:
                    menu_item["modifications"]["Required"].append(modification_name)
                elif specification["required"] == False:
                    for value in specification["values"]:
                        modification_name = value["name"]["en-US"]
                        modification_name = modification_name.rstrip(' ')
                        menu_item["modifications"]["Optional"].append(modification_name)

            for attribute in raw_item["attributes"]:
                modification_name = attribute["name"]["en-US"]
                modification_name = modification_name.rstrip(' ')

                if modification_name == "Specifications":
                    menu_item["modifications"]["Required"].append("Size")
                else:
                    menu_item["modifications"]["Optional"].append(modification_name)

            for addOnRef in raw_item["addOnRefs"]:
                for value in addOnRef["values"]:
                    modification_name = value["name"]["en-US"]
                    modification_name = modification_name.rstrip(' ')
                    menu_item["modifications"]["Optional"].append(modification_name)

            if item_name in self.item_desc:
                menu_item["Description"] = self.item_desc[item_name]
            else:
                print(f"Item {item_name} not found in description file.")
                menu_item["Description"] = item_name

            menu_dict[item_name] = menu_item

        return menu_dict
    
    def load_category(self):
        """
        Load category from menu

        return:
            dict of category to name mapping:
                key: category name
                value: list of item names in the category
        """

        category_to_items = {}
        for item_name, item_info in self.items_info.items():
            category = item_info["Category"]

            if category in ['Featured Items', 'Milktea Specialty']:
                category = 'Milk Tea'

            if category in ["Teaspresso"]:
                category = 'Teaspresso'

            if category in ['Itea Jelly Series']:
                category = 'Jelly Tea'
            
            if category in ['Sea Salt Kreama']:
                category = 'Sea Salt Tea'

            if category in ['Signature Iced Milk & Sago']:
                category = 'Milk & Sago'

            if category in ['Itea Fruit Tea']:
                category = 'Fruit Tea'
            
            if category in ['Summer Frosty']:
                category = 'Frosty Blends'

            if category in ['Hot Drink']:
                category = 'Hot Drinks'

            if category in ['Snacks']:
                category = 'Snacks'

            if category in ['Noodle & Rice']:
                category = 'Meals'

            if category not in category_to_items:
                category_to_items[category] = set()
            category_to_items[category].add(item_name)

        for category, item_names in category_to_items.items():
            category_to_items[category] = list(item_names)

        return category_to_items

    def load_modification(self):
        """
        return:
            dict of modification spec
                
            key: modification name
            value: {
                "name": cust_name,
                "description": cust_name,
                "values": cust_spec,
                "options": {
                    "name": cust_name,
                    "description": cust_desc,
                }
            }
        """

        with open(self.menu_path, 'r', encoding='utf-8') as f:
            menu = json.load(f)

        modification_dict = {}
        for raw_item in menu:
            for specification in raw_item['specifications']:
                cust_name = specification["name"]["en-US"].rstrip()
                if cust_name not in modification_dict:
                    modification_dict[cust_name] = specification
             
            for attribute in raw_item["attributes"]:
                cust_name = attribute["name"]["en-US"].rstrip()
                if cust_name not in modification_dict:
                    modification_dict[cust_name] = attribute

            for addOnRef in raw_item["addOnRefs"]:
                for value in addOnRef["values"]:
                    cust_name = value["name"]["en-US"].rstrip()
                    if cust_name not in modification_dict:
                        modification_dict[cust_name] = value

        return_dict = {}
        for cust_name, cust_spec in modification_dict.items():
            
            if cust_name == "Specifications":
                cust_name = "Size"

            if cust_name == "Modifications":
                continue  

            if cust_name in self.custom_desc:
                return_dict[cust_name] = {
                    "name": cust_name,
                    "description": self.custom_desc[cust_name],
                    "values": cust_spec,
                    "options": None
                }

            else:
                print(f"modification {cust_name} {cust_spec} not found in description file.")
                
                return_dict[cust_name] = {
                    "name": cust_name,
                    "description": cust_name,
                    "values": cust_spec,
                    "options": None
                }

            if cust_name == "Size":
                return_dict[cust_name]["options"] = [{"name": "Regular",
                                                        "description": "Regular or Small size"}, 
                                                     {"name": "Large",
                                                        "description": "Large size",}]
            
            if cust_name == "Sugar":
                return_dict[cust_name]["options"] = [{
                    "name": "0% Sugar",
                    "description": "No sugar"
                }, {
                    "name": "30% Sugar",
                    "description": "less sugar"
                }, {
                    "name": "50% Sugar",
                    "description": "half sugar"
                }, {
                    "name": "80% Sugar",
                    "description": "more than half sugar"
                }, {
                    "name": "100% Sugar",
                    "description": "full sugar"
                }, {
                    "name": "110% Sugar",
                    "description": "extra sugar"
                }]
              
            if cust_name == "Ice":
                return_dict[cust_name]["options"] = [
                    {
                        "name": "0% Ice",
                        "description": "No ice"
                    }, {
                        "name": "30% Ice",
                        "description": "less ice"
                    }, {
                        "name": "50% Ice",
                        "description": "half ice"
                    }, {
                        "name": "80% Ice",
                        "description": "more than half ice"
                    }, {
                        "name": "100% Ice",
                        "description": "full ice"
                    }, {
                        "name": "110% Ice",
                        "description": "extra ice"
                    }
                ]

            if cust_name == "Tea":
                return_dict[cust_name]["options"] = [
                    {
                        "name": "Green Tea",
                        "description": "Green Tea"
                    }, {
                        "name": "Black Tea",
                        "description": "Black Tea"
                    }
                ]
        return return_dict
    
    def get_items(self):
        """
        Get all items

        return:
            list of item names
        """
        return self.items_info
    
    def get_items_by_category(self, category):
        """
        Get items in a category

        return:
            list of item names
        """

        return self.items_by_category[category]

    def get_item_info(self, item_name):
        """
        Get item information

        return:
            dict of item information:
                key: item name
                value: item information
        """

        return self.items_info[item_name]
    
    def get_modifications_by_item(self, item_name, modification_type = "All"):
        """
        Get modifications of an item

        return:
            List of modifications:
        """
        if modification_type != "All" and modification_type != "Required" and modification_type != "Optional":
            print("Invalid modification type")
            return []
        
        if modification_type == "All":
            return self.items_info[item_name]["modifications"]["Required"] + self.items_info[item_name]["modifications"]["Optional"]
        
        if modification_type == "Required":
            return self.items_info[item_name]["modifications"]["Required"]
        
        if modification_type == "Optional":
            return self.items_info[item_name]["modifications"]["Optional"]


    def get_modification_info(self, modification_name):
        """
        Get modification spec

        return:
            dict of modification spec
        """

        return self.custom_info[modification_name]

    def get_item_price(self, item_name, modifications):
        """
        Get price of an item with modifications

        return:
            price of the item
        """

        return 0

    def get_all_category_info(self):
        """
        Get category description

        return:
            dict of category to category description
        """
        return self.category_info