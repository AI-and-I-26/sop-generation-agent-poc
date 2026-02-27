import boto3
import json

# Initialize Bedrock Runtime client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-2'
)

# Test with Llama 3.1 8B
model_id = 'us.meta.llama3-3-70b-instruct-v1:0'

# Prepare request
prompt = """Explain what a Standard Operating Procedure (SOP) is in one paragraph."""

request_body = {
    "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
    "max_gen_len": 512,
    "temperature": 0.7,
    "top_p": 0.9
}

# Invoke model
response = bedrock_runtime.invoke_model(
    modelId=model_id,
    body=json.dumps(request_body)
)

# Parse response
response_body = json.loads(response['body'].read())
generated_text = response_body['generation']

print("Generated Response:")
print(generated_text)
