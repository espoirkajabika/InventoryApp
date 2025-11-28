import json
import boto3
from decimal import Decimal
import ulid

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
    Lambda function to add a new inventory item to DynamoDB.
    
    API Endpoint: POST /item
    
    Request Body:
        name (string): Name of the item.
        description (string): Description of the item.
        qty_on_hand (integer): Quantity on hand.
        price (float): Price of the item.
        location_id (integer): Location ID where item is stored.
    
    Returns:
        dict: Response containing the created item or error message.
    """
    try:
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event.get('body', '{}'))
        else:
            body = event.get('body', {})
        
        # Validate required fields
        required_fields = ['name', 'description', 'qty_on_hand', 'price', 'location_id']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                })
            }
        
        # Generate a new ULID for the item
        item_id = str(ulid.new())
        
        # Create the item object
        item = {
            'id': item_id,
            'name': body['name'],
            'description': body['description'],
            'qty_on_hand': int(body['qty_on_hand']),
            'price': Decimal(str(body['price'])),
            'location_id': int(body['location_id'])
        }
        
        # Put the item into DynamoDB
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Successfully created inventory item',
                'item': item
            }, cls=DecimalEncoder)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Error creating inventory item',
                'error': str(e)
            })
        }
