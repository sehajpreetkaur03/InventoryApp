import json
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "Inventory"
table = dynamodb.Table(TABLE_NAME)


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
    GET /location/{id}
    Returns all inventory items at the given location_id.
    """

    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    # 🔹 Look for BOTH "id" and "location_id"
    location_id = (
        path_params.get("id")
        or path_params.get("location_id")
        or (query_params.get("id") if query_params else None)
        or (query_params.get("location_id") if query_params else None)
    )

    if not location_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing location id"})
        }

    try:
        location_id_num = int(location_id)

        # Use correct field name from your table: location_id
        response = table.scan(
            FilterExpression=Attr("location_id").eq(location_id_num)
        )

        items = response.get("Items", [])
        items = _convert_decimal(items)

        return {
            "statusCode": 200,
            "body": json.dumps(items)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error retrieving items for location",
                "error": str(e),
            }),
        }
