import json
def loadJsonConfig(config_file_name="../../configs/config.json"):
    with open (config_file_name,"r") as json_file:
        return  json.load(json_file)
