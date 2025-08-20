import json
import os
import boto3
from utils.utils import build_response

dynamodb = boto3.resource('dynamodb')
goal_table = os.environ['GOALS_TABLE_NAME']
table = dynamodb.Table(goal_table)

def lambda_handler(event, context):
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        goal_id = event['pathParameters']['id']

        response = table.get_item(Key={
            'userId': user_id,
            'goalId': goal_id
        })
        item = response.get('Item')

        if not item:
            return build_response(404, {'error': 'Goal not found or not authorized'})
        
        table.delete_item(Key={
            'userId': user_id,
            'goalId': goal_id
        })
        return build_response(200, {'message': 'Goal successfully deleted'})
    
    except Exception as e:
        print(f"Error: {e}")
        return build_response(500, {'error': str(e)})
