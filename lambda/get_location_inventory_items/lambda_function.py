import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')

# GSI name - assumes the GSI has location_id as partition key and id as sort key
GSI_NAME = 'location_id-id-index'


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal objects to float for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Lambda function to retrieve all inventory items in a specific location.
    Uses the Global Secondary Index (GSI) with reversed PK/SK for efficient querying.
    
    API Endpoint: GET /location/{id}
    
    Path Parameters:
        id (integer): The location ID to query.
    
    Returns:
        dict: Response containing all items in the specified location or error message.
    """
    try:
        # Extract the location ID from path parameters
        location_id = event.get('pathParameters', {}).get('id')
        
        if not location_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Missing location ID in path parameters'
                })
            }
        
        # Convert location_id to integer
        try:
            location_id = int(location_id)
        except ValueError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Location ID must be an integer'
                })
            }
        
        # Query the GSI to get all items in this location
        response = table.query(
            IndexName=GSI_NAME,
            KeyConditionExpression=Key('location_id').eq(location_id)
        )
        
        items = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName=GSI_NAME,
                KeyConditionExpression=Key('location_id').eq(location_id),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Successfully retrieved inventory items for location {location_id}',
                'location_id': location_id,
                'count': len(items),
                'items': items
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
                'message': 'Error retrieving inventory items for location',
                'error': str(e)
            })
        }
