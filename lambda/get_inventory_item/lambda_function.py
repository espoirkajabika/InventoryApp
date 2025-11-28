import json
import boto3
from decimal import Decimal

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal objects to float for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Lambda function to retrieve a specific inventory item by ID.
    
    API Endpoint: GET /item/{id}
    
    Path Parameters:
        id (string): The ULID of the inventory item.
    
    Returns:
        dict: Response containing the inventory item or error message.
    """
    try:
        # Extract the item ID from path parameters
        item_id = event.get('pathParameters', {}).get('id')
        
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Missing item ID in path parameters'
                })
            }
        
        # Query the table using the partition key (id)
        # Since we need to find the item without knowing location_id,
        # we'll query using the id and get all items with that id
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq(item_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': f'Item with ID {item_id} not found'
                })
            }
        
        # Return the first (and should be only) item
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Successfully retrieved inventory item',
                'item': items[0]
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Error retrieving inventory item',
                'error': str(e)
            })
        }
