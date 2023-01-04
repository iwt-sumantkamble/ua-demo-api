import logging
import os

import boto3

from constant import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])


def get_all():
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return data


def get_by_id(item_id):
    response = table.get_item(Key={ID: item_id})
    return response[ITEM] if ITEM in response else None
