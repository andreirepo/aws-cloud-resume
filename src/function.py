import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PageVisits')

def lambda_handler(event, context):
    """
    Lambda function to track page visits.
    GET: Returns visit count for a page
    POST: Increments visit count for a page
    """
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            page_path = params.get('page_path', '/')
            
            # Get current count
            response = table.query(
                KeyConditionExpression=Key('page_path').eq(page_path)
            )
            
            count = 0
            if response['Items']:
                count = response['Items'][0]['visit_count']
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'page_path': page_path,
                    'visit_count': count
                })
            }
            
        elif http_method == 'POST':
            # Get page path from request body
            body = json.loads(event.get('body', '{}'))
            page_path = body.get('page_path', '/')
            
            # Update visit count
            response = table.update_item(
                Key={'page_path': page_path},
                UpdateExpression='SET visit_count = if_not_exists(visit_count, :start) + :inc, last_visit = :time',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':start': 0,
                    ':time': datetime.utcnow().isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'page_path': page_path,
                    'visit_count': response['Attributes']['visit_count']
                })
            }
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Method not supported'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }