import os
import json
import random
import string
import re
from datetime import datetime, timedelta
from typing import TypedDict
import decimal
import boto3

TOKEN_SIZE = 32
TOKEN_PARAM = 'token'
TOKENS_DB_NAME = os.environ['TOKEN_TABLE_NAME']
POLL_DB_NAME = os.environ['POLL_TABLE_NAME']
EXPIRE_TIME = timedelta(hours=24)
db = boto3.resource('dynamodb')
tokensTable = db.Table(TOKENS_DB_NAME)
pollTable = db.Table(POLL_DB_NAME)
"""
{
  "polls": [
    {
      "class": "CSE3903",
      "x": 1500,
      "y": 12,
      "type": "difficulty-usefullness"
    },
    {
      "class": "CSE3903",
      "x": 1500,
      "y": 12,
      "type": "difficulty-usefullness"
    }
  ],
  "token": "my_token"
}
"""

# TODO get from s3 or other source
VALID_DEPARTMENTS = ['CSE']
VALID_CLASSES = {
    'CSE': ['3903']
}
VALID_TYPES = ['difficulty-usefulness']
MAX_AXIS = 1
MIN_AXIS = -1


# Must use functional syntax becase class is a keyword
# Deprecated since version 3.11, will be removed in version 3.13
Poll = TypedDict('Poll', {'class': str, 'type': str, 'x': float, 'y': float})


def lambda_handler(event, context):
    if TOKEN_PARAM not in event:
        return buildError(f'No ${TOKEN_PARAM} provided')

    # === Validate token ===
    token = event[TOKEN_PARAM]
    current_time = datetime.now()
    current_timestamp = round(current_time.timestamp())

    print('Validating token.')
    tokenRtn = tokensTable.get_item(
        Key={
            'token': token
        }
    )

    if ('Item' not in tokenRtn or
        tokenRtn['Item']['expires_at'] < current_timestamp or
            tokenRtn['Item']['used']):
        return buildError('Not a valid token.')

    print('Token valid.')

    # === Parse poll ===
    if "polls" not in event or type(event['polls']) != list or len(event['polls']) == 0:
        return buildError("No polls in request.")

    validatedPolls = []
    for rawPoll in event['polls']:
        poll = Poll(rawPoll)
        try:
            validatePoll(poll)
        except ValidationError as e:
            print(f"Error while validating poll: {rawPoll}")
            return buildError(str(e))
        validatedPolls.append(poll)

    # Polls are input validated
    for poll in validatedPolls:
        # === Write poll ===
        writePoll(poll, current_timestamp, token, tokenRtn['Item']['email'])

    invalidateToken(tokenRtn['Item'])

    return buildSuccess(tokenRtn)


def validatePoll(poll: Poll):
    if ('class' not in poll or
        'type' not in poll or
        'x' not in poll or
            'y' not in poll):
        raise ValidationError("Missing fields in poll.")

    # Class
    classs = poll['class']
    if type(classs) is not str:
        raise ValidationError("Invalid class.")
    splitOut = splitClass(classs)
    print(f'split out: {splitOut}')
    if len(splitOut) != 3:
        raise ValidationError("Invalid class.")
    department = splitOut[1]
    classNumber = splitOut[2]
    if (department not in VALID_DEPARTMENTS or
            classNumber not in VALID_CLASSES[department]):
        raise ValidationError("Invalid class.")

    # Type
    if (type(poll['type']) is not str or
        poll['type'] not in VALID_TYPES):
        raise ValidationError("Invalid type.")

    x = poll['x']
    y = poll['y']
    if type(x) is int:
        x = float(x)
    if type(y) is int:
        y = float(y)
    # x/y
    if (type(x) is not float or type(y) is not float or
        x > MAX_AXIS or x < MIN_AXIS or
        y > MAX_AXIS or y < MIN_AXIS):
        raise ValidationError("Invalid value for x/y.")

def splitClass(classs: str):
    return re.split(r'(^[^\d]+)', classs)

# Writes poll to polls dynmodb dtabase
def writePoll(poll: Poll, currentTimestamp: int,
              token: str, email: str):
    print(f'Writing poll: {poll}')
    item = {}
    splitOut = splitClass(poll['class'])
    item['class'] = splitOut[1] + '#' + splitOut[2]
    item['x'] = decimal.Decimal(str(poll['x']))
    item['y'] = decimal.Decimal(str(poll['y']))
    item['updated_at'] = currentTimestamp
    item['token'] = token
    item['type-email'] = poll['type'] + '#' + email
    prtn = pollTable.put_item(
        Item=item
    )


def invalidateToken(item: dict):
    print('Invalidating token.')
    item['used']=True
    putRtn=tokensTable.put_item(
        Item = item
    )


class ValidationError(Exception):
    pass


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
