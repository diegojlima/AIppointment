# Lambda Module Upgrade: terraform-aws-lambda

This branch upgrades the Lambda deployment approach to use the community standard terraform-aws-lambda module, which is a widely adopted module for managing Lambda functions.

## Changes Made

1. **Replaced Custom Module with Community Module**
   - Modified `infrastructure/modules/cloud_function` to use the terraform-aws-lambda module internally
   - Maintained the same interface for backward compatibility

2. **Fixed Path References**
   - Replaced relative paths (`../../../`) with stable path references (`${path.root}/`)
   - This eliminates the path resolution issues in GitHub Actions

3. **Enhanced GitHub Actions Workflow**
   - Added verification step to ensure Lambda packages exist before Terraform runs
   - Improved logging and debugging capabilities

## Benefits

- **Reliability**: The terraform-aws-lambda module is community-maintained and thoroughly tested
- **Path Stability**: Using `${path.root}` ensures consistent path resolution across environments
- **Better Error Handling**: Module has proper error messages and validation
- **Future Extensibility**: Module supports advanced features we might need in the future:
  - Source directory packaging (no need for pre-built ZIPs)
  - Layer management
  - Automatic dependency handling
  - Container image support

## Backward Compatibility

This implementation preserves all outputs and inputs from the original module, ensuring backward compatibility with the rest of the codebase.

## How to Test

1. Run the GitHub workflow manually via workflow_dispatch
2. Verify that Lambda functions are created successfully
3. Verify Bedrock Agent integration continues to work