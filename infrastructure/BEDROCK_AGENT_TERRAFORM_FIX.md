# Bedrock Agent Terraform Fix

## Issue

The Terraform validation error occurred because:

1. The AWS provider being used doesn't support the `aws_bedrock_agent` resource type
2. The correct resource name is `aws_bedrockagent_agent` (note the difference: `bedrockagent` vs `bedrock_agent`)
3. This resource is available in AWS Provider version 5.48.0 and newer

## Changes Made

1. Added a `versions.tf` file to specify the minimum AWS provider version:
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.48.0"
    }
  }
  required_version = ">= 1.0.0"
}
```

2. Updated resource names in `modules/bedrock_agent/main.tf`:
   - `aws_bedrock_agent` → `aws_bedrockagent_agent`
   - `aws_bedrock_agent_api_schema` → `aws_bedrockagent_agent_api_schema`
   - `aws_bedrock_agent_alias` → `aws_bedrockagent_agent_alias`
   - `aws_bedrock_agent_action_group` → `aws_bedrockagent_agent_action_group`

3. Updated parameter names:
   - `foundation_model_id` → `foundation_model`

4. Updated the `outputs.tf` file to match the new resource names

## Testing

To test these changes locally, run:

```bash
cd infrastructure/global/terraform
terraform init
terraform validate
```

This should resolve the validation errors.

## Documentation References

- [AWS Bedrock Agent Terraform Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bedrockagent_agent)
- [AWS CloudFormation Bedrock Agent](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-bedrock-agent.html)
