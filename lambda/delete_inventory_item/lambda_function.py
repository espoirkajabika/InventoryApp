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
    Lambda function to delete a specific inventory item by ID.
    
    API Endpoint: DELETE /item/{id}
    
    Path Parameters:
        id (string): The ULID of the inventory item to delete.
    
    Returns:
        dict: Response confirming deletion or error message.
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
        
        # First, query to find the item and get its location_id (sort key)
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
        
        # Get the item to delete (includes location_id)
        item_to_delete = items[0]
        
        # Delete the item using both partition key and sort key
        table.delete_item(
            Key={
                'id': item_id,
                'location_id': item_to_delete['location_id']
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Successfully deleted inventory item with ID {item_id}',
                'deleted_item': item_to_delete
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
                'message': 'Error deleting inventory item',
                'error': str(e)
            })
        }
