import os
import json
import random
import string
import re
from datetime import datetime, timedelta
from typing import TypedDict
from decimal import Decimal
import boto3
from boto3.dynamodb.types import TypeDeserializer

serializer = TypeDeserializer()

STATISTICS_DB_NAME = os.environ['STATISTICS_TABLE_NAME']
db = boto3.resource('dynamodb')
statisticsTable = db.Table(STATISTICS_DB_NAME)

EVENT_INSERT = 'INSERT'
EVENT_MODIFY = 'MODIFY'
EVENT_REMOVE = 'REMOVE'

# Must use functional syntax becase class is a keyword
# Deprecated since version 3.11, will be removed in version 3.13
Poll = TypedDict('Poll', {'class': str, 'type': str, 'x': float, 'y': float})

STAT_STR_PARAMS = ['class', 'type']
STAT_NUM_PARAMS = ['avgx', 'avgy', 'varx', 'vary', 'sumx', 'sumy', 'numx', 'numy']
StatDict = TypedDict('StatDict', {
    'class': str,
    'type': str,
    'avgx': float,
    'avgy': float,
    'varx': float,
    'vary': float,
    'sumx': float,
    'sumy': float,
    'numx': float,
    'numy': float})
StatItem = TypedDict('StatItem', {
    'class': str,
    'type': str,
    'avgx': Decimal,
    'avgy': Decimal,
    'varx': Decimal,
    'vary': Decimal,
    'sumx': Decimal,
    'sumy': Decimal,
    'numx': Decimal,
    'numy': Decimal})
# https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_streams_StreamRecord.html#DDB-Type-streams_StreamRecord-NewImage


def lambda_handler(event, context):
    for record in event['Records']:
        print(f'Processing record {record}')
        dbrecord = record['dynamodb']

        # Get current statistics item
        keys = dbrecord['Keys']
        classs = keys['class']['S']
        typee = keys['type-email']['S'].split('#')[0]
        srtn = statisticsTable.get_item(
            Key={
                'class': classs,
                'type': typee
            }
        )

        curStats = defaultStatDict()
        if 'Item' in srtn:
            curStats = parseStatisticItem(srtn['Item'])
        
        print(srtn)
        
        if record['eventName'] == EVENT_INSERT:
            newPoll = deserialize(record['NewImage'])

        


    return buildSuccess(event)


def parseStatisticItem(item: StatItem) -> StatDict:
    rtn = {}
    for key in STAT_STR_PARAMS:
        rtn[key] = item[key]
    for key in STAT_NUM_PARAMS:
        rtn[key] = float(item[key])

    return rtn

def convertStatisticItem(dict: StatDict) -> StatItem:
    rtn = {}
    for key in STAT_STR_PARAMS:
        rtn[key] = dict[key]
    for key in STAT_NUM_PARAMS:
        rtn[key] = Decimal(str(dict[key]))

    return rtn
    
def defaultStatDict(classs: str, typee: str) -> StatDict:
    rtn = {}
    rtn['class'] = classs
    rtn['type'] = typee
    for key in STAT_NUM_PARAMS:
        rtn[key] = 0.0

    return rtn


def buildResponse() -> dict:
    # Return 200 status code (even for errors)
    # Errors are respored in body
    return {}


def buildError(message: string) -> dict:
    print(f"ERROR: {message}")
    response=buildResponse()
    response['statusCode']=401
    body={'message': message}
    response['body']=body
    return response


def buildSuccess(data: dict) -> dict:
    response=buildResponse()
    response['statusCode']=200
    response['body']=data
    return response


def deserialize(data):
    if isinstance(data, list):
        return [deserialize(v) for v in data]

    if isinstance(data, dict):
        try:
            return serializer.deserialize(data)
        except TypeError:
            return {k: deserialize(v) for k, v in data.items()}
    else:
        return data
