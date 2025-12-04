import json
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


# Same Decimal helper style as in the slides
def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def lambda_handler(event, context):
    # DynamoDB setup
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Inventory')

    # Get the id from the PATH, not query string
    if 'pathParameters' not in event or 'id' not in event['pathParameters']:
        return {
            'statusCode': 400,
            'body': json.dumps("Missing 'id' path parameter")
        }

    item_id = event['pathParameters']['id']

    try:
        # Query by partition key item_id (similar to get-one-row style)
        response = table.query(
            KeyConditionExpression=Key('item_id').eq(item_id)
        )
        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps("Item not found")
            }

        items = convert_decimals(items)

        return {
            'statusCode': 200,
            'body': json.dumps(items)
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
