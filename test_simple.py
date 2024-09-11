import boto3
from moto import mock_aws

@mock_aws
def test_my_dynamodb_function():
    # Setup your DynamoDB mock
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create a DynamoDB table
    table = dynamodb.create_table(
        TableName='my-table',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    
    # Add your logic to test here
    table.put_item(Item={'id': '123', 'data': 'example'})
    
    # Fetch the item from the mock table and assert
    response = table.get_item(Key={'id': '123'})
    assert response['Item']['data'] == 'example'
