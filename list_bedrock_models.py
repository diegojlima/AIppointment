import boto3

def list_bedrock_models():
    bedrock = boto3.client(service_name="bedrock", region_name='us-west-2')
    response = bedrock.list_foundation_models(byProvider="anthropic")

    print("Available models:")
    for summary in response.get("modelSummaries", []):
        print(summary["modelId"])

list_bedrock_models()
