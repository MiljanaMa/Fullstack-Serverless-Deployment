import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from utils.utils import build_response

dynamodb = boto3.resource('dynamodb')
goal_table = os.environ['GOALS_TABLE_NAME']
table = dynamodb.Table(goal_table)

def lambda_handler(event, context):
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        print({"email": event['requestContext']['authorizer']['claims']['email']})
        response = table.query(
            KeyConditionExpression=Key('userId').eq(str(user_id))
        )

        goals = response.get('Items', [])

        return build_response(200, goals)

    except Exception as e:
        print(f"Error: {e}")
        return build_response(500, {'error': str(e)})
    