import pandas
import io
import boto3
import json
from botocore.exceptions import ClientError
from io import StringIO
bucket = 'question-bank-for-validators'

def write_file_to_s3(file_name,data_json):
    df = pandas.DataFrame(data_json)
    df.to_excel(file_name +'.xlsx', index=False)
    file_path = 'mathematics/' + file_name +'.xlsx'
    print(file_path)
    s3 = boto3.client('s3')
    try:
        response = s3.upload_file(file_name +'.xlsx', bucket, file_path)
    except ClientError as e:
        logging.error(e)
        return False
    return True 