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
        body = json.loads(event['body'])

        response = table.get_item(Key={
            'userId': user_id,
            'goalId': goal_id
        })
        item = response.get('Item')

        if not item:
            return build_response(404, {'error': 'Goal not found or not authorized'})
        
        updated_attributes = {}
        if 'title' in body:
            updated_attributes['title'] = body['title']
        if 'content' in body:
            updated_attributes['content'] = body['content']

        if not updated_attributes:
            return build_response(400, {'error': 'No fields to update'})
        
        update_expression = "SET " + ", ".join(f"{k}=:{k}" for k in updated_attributes)
        expression_attribute_values = {f":{k}": v for k, v in updated_attributes.items()}

        table.update_item(
            Key={
            'userId': user_id,
            'goalId': goal_id
            },
            UpdateExpression = update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        item.update(updated_attributes)

        return build_response(200, item)

    except Exception as e:
        print(f"Error: {e}")
        return build_response(500, {'error': str(e)})
