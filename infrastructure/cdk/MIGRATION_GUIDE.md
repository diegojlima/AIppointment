# Terraform to CDK Migration Guide for AIppointment

This guide provides instructions for migrating the AIppointment project infrastructure from Terraform to AWS CDK.

## Migration Strategy

The migration follows a parallel deployment approach, where both Terraform and CDK deployments can coexist during the transition period. This allows for gradual migration and thorough testing before fully switching to CDK.

## Prerequisites

1. Install AWS CDK CLI:
```
npm install -g aws-cdk
```

2. Set up Python environment:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure AWS credentials with appropriate permissions

## Step-by-Step Migration

### 1. Infrastructure Component Mapping

| Terraform Resource | CDK Construct |
|-----------------|--------------|
| `aws_dynamodb_table` | `dynamodb.Table` |
| `aws_lambda_function` | `lambda_.Function` |
| `aws_apigatewayv2_api` | `apigatewayv2.HttpApi` |
| `aws_s3_bucket` | `s3.Bucket` |
| `aws_iam_role` | `iam.Role` |
| `aws_bedrockagent_agent` | Custom resource (no native L2 construct yet) |

### 2. Deployment Strategy

#### First deployment:
1. Deploy only non-critical resources using CDK
2. Verify they match the existing Terraform-managed resources
3. Gradually add more resource types

#### Resource importation (optional):
The CDK provides ways to import existing resources:
```python
# Example: Import existing DynamoDB table
dynamodb.Table.from_table_name(
    self, "ImportedTable", "existing-table-name"
)
```

### 3. State Management

- Terraform state is stored in S3 and DynamoDB
- CDK uses CloudFormation, which manages its own state
- Resources can't be managed by both systems simultaneously

### 4. Testing the Migration

1. Deploy to a test environment first
2. Compare resources using AWS CLI or Console
3. Test functionality of deployed services
4. Verify that Lambda functions work correctly

### 5. Handling Bedrock Agent Resources

The Bedrock Agent resources don't have native L2 constructs in CDK yet, so we use a custom resource with a Lambda function to create and manage them. The implementation closely follows the Terraform configuration.

### 6. Cutover Process

1. Deploy all resources with CDK
2. Verify functionality
3. Update any external references to point to new resources
4. Back up Terraform state
5. Run `terraform state rm` commands to remove resources from Terraform state

## Terraform vs CDK Reference

### DynamoDB Table

**Terraform:**
```terraform
resource "aws_dynamodb_table" "appointments" {
  name           = "${local.project_name}-appointments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PhoneNumber"
  range_key      = "CreatedAt"

  attribute {
    name = "PhoneNumber"
    type = "S"
  }

  attribute {
    name = "CreatedAt"
    type = "S"
  }
}
```

**CDK (Python):**
```python
appointments_table = dynamodb.Table(
    self, "AppointmentsTable",
    table_name=f"{project_name}-appointments",
    partition_key=dynamodb.Attribute(
        name="PhoneNumber",
        type=dynamodb.AttributeType.STRING
    ),
    sort_key=dynamodb.Attribute(
        name="CreatedAt",
        type=dynamodb.AttributeType.STRING
    ),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    removal_policy=RemovalPolicy.RETAIN,
)
```

### Lambda Function

**Terraform:**
```terraform
resource "aws_lambda_function" "function" {
  filename         = var.lambda_zip_file
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = var.handler
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = var.environment_variables
  }
}
```

**CDK (Python):**
```python
lambda_function = lambda_.Function(
    self, "MyFunction",
    function_name=function_name,
    runtime=lambda_.Runtime.PYTHON_3_12,
    handler=handler,
    code=lambda_.Code.from_asset(lambda_code_path),
    environment=environment_variables,
    timeout=Duration.seconds(timeout),
    memory_size=memory_size,
    role=lambda_role,
)
```

## Rollback Plan

If issues occur during migration:

1. Identify the problematic resources
2. Revert to using the Terraform-managed resources
3. Run `cdk destroy` to remove CDK-managed resources if needed
4. Document the issues for future migration attempts

## Post-Migration Tasks

1. Remove Terraform configuration files (or archive them)
2. Update CI/CD pipelines to use CDK
3. Update documentation
4. Train team members on CDK concepts and usage
