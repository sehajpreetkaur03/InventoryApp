import json
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "Inventory"
table = dynamodb.Table(TABLE_NAME)

# Read key schema from the table (e.g. item_id, item_location_id)
KEY_ATTRS = [k["AttributeName"] for k in table.key_schema]


def _convert_decimal(value):
    if isinstance(value, list):
        return [_convert_decimal(v) for v in value]
    if isinstance(value, dict):
        return {k: _convert_decimal(v) for k, v in value.items()}
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    return value


def lambda_handler(event, context):
    """
    DELETE /item/{id}
    Deletes all inventory records with the given item_id.
    """

    # Get id from path: /item/{id}
    path_params = event.get("pathParameters") or {}
    item_id = (
        path_params.get("id")
        or path_params.get("item_id")
        or event.get("item_id")
    )

    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item id"})
        }

    try:
        # We assume the partition key in the table is 'item_id'
        # (this already works in your other Lambdas)
        query_response = table.query(
            KeyConditionExpression=Key("item_id").eq(item_id)
        )
        items = query_response.get("Items", [])

        if not items:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Item not found"})
            }

        deleted_count = 0

        for item in items:
            # Build the DynamoDB key exactly as the table expects it
            # (only attributes from key schema)
            key = {attr: item[attr] for attr in KEY_ATTRS}

            table.delete_item(Key=key)
            deleted_count += 1

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Item deleted successfully",
                "item_id": item_id,
                "deleted_records": deleted_count
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error deleting item",
                "error": str(e),
            }),
        }
