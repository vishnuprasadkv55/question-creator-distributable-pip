import pandas
import io
import boto3
import json
bucket = 'question-bank-for-validators'

def load_data_from_s3(file_name):
    file_path = 'mathematics/' + file_name +'.xlsx'
    s3 = boto3.client('s3')
    excel_data_fragment_obj = s3.get_object(Bucket=bucket, Key=file_path)
    
    excel_data_fragment = pandas.read_excel(io.BytesIO(excel_data_fragment_obj['Body'].read()))
    json_str = excel_data_fragment.to_json(orient='records')
    json_object = json.loads(json_str)
    return json_object