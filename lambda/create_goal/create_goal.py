import json
import os
from datetime import datetime
import time
import uuid
import boto3
from utils.utils import build_response


dynamodb = boto3.resource('dynamodb')

goal_table = os.environ['GOALS_TABLE_NAME']

table = dynamodb.Table(goal_table)

def lambda_handler(event, context):
    try:
        
        body = json.loads(event.get('body', '{}'))
        title = body.get('title')
        content = body.get('content')

        if not title or not content:
           return build_response(400, {'error': 'Missing required fields: title or content'})

        if title == "a":
            time.sleep(3)

        if title == "b":
            raise Exception('Title "a" is not allowed')
            
        user_id = event['requestContext']['authorizer']['claims']['sub']

        goal_id = str(uuid.uuid4())

        goal_item = {
            'userId': user_id,
            'goalId': goal_id,
            'title': title,
            'content': content,
            'createdAt': datetime.now().isoformat()
        }

        table.put_item(Item=goal_item)
        return build_response(200, goal_item)
    
    except Exception as e:
        error_log = {
            "status": 500,
            "error": f"{e}"
        }
        print(json.dumps(error_log))
        return build_response(500, {'error': 'Internal server error'})
