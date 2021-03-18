import pandas
import os
import json

def initialize_data(file_name):
    # excel_data_fragment = pandas.read_excel(os.getcwd()+ '\Sent\Sent\data_Example_set_unfiltered.xlsx')
    excel_data_fragment = pandas.read_excel('https://github.com/vishnuprasadkv55/question-bank/raw/master/data_1/' + file_name + '.xlsx')
    json_str = excel_data_fragment.to_json(orient='records')
    json_object = json.loads(json_str)
    return json_object

def get_data_by_index(json_object, item_index):
    return json_object[item_index]