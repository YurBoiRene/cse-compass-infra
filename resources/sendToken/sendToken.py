import os
import json
import random
import string
import re
from datetime import datetime, timedelta
import boto3

TOKEN_SIZE = 32
EMAIL_PARAM = 'email'
TOKENS_DB_NAME = os.environ['TOKEN_TABLE_NAME']
EMAIL_INDEX_NAME = os.environ['EMAIL_INDEX_NAME']
EXPIRE_TIME = timedelta(hours=24)
db = boto3.resource('dynamodb')
table = db.Table(TOKENS_DB_NAME)

def lambda_handler(event, context):
    if EMAIL_PARAM not in event:
        return buildError(f'No email parameter provided')
    
    email = event['email'].lower()
    # regex match for osu email
    match = re.match(r'[a-z]+\.[1-9]\d*@osu\.edu', email)
    if match == None:
        return buildError(f'Not a valid OSU email')
    email = email[match.start():match.end()]

    current_time = datetime.now()
    current_timestamp = round(current_time.timestamp())
    
    qrtn = table.query(
        IndexName=EMAIL_INDEX_NAME,
        KeyConditionExpression=
            boto3.dynamodb.conditions.Key('email').eq(email) &
            boto3.dynamodb.conditions.Key('expires_at').gt(current_timestamp));
        
    # Check if has valid token already
    for item in qrtn['Items']:
        if item['used'] == False:
            return buildError('Email already has active token.')
    
    # Todo check email
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=TOKEN_SIZE))
    
    
    expire_time = current_time + EXPIRE_TIME
    expire_timestamp = round(expire_time.timestamp())
    
    rtn = table.put_item(
        Item={
            'token': token,
            'email': email,
            'created_at': current_timestamp,
            'expires_at': expire_timestamp,
            'used': False
        })
    
    return buildSuccess({'expires_at': expire_timestamp})

def buildResponse() -> dict:
    # Return 200 status code (even for errors)
    # Errors are respored in body
    return {}

def buildError(message: string) -> dict:
    response = buildResponse()
    response['statusCode'] = 401
    body = {'message': message}
    response['body'] = body
    return response

def buildSuccess(data: dict) -> dict:
    response = buildResponse()
    response['statusCode'] = 200
    response['body'] = data
    return response