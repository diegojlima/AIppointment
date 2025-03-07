# AIppointment CDK Deployment Instructions

## Prerequisites

Before deploying the CDK application, ensure you have the following prerequisites:

1. **AWS CLI** installed and configured with appropriate credentials
2. **Node.js** and **npm** installed (required for the CDK CLI)
3. **AWS CDK CLI** installed globally: `npm install -g aws-cdk`
4. **Python 3.8+** installed
5. **Virtual environment** created and activated

## Known Issues

When setting up the CDK environment, you might encounter the following issue:

```
ModuleNotFoundError: No module named 'constructs._jsii'
```

This is typically caused by an incompatibility between the version of the `jsii` package and the version of `constructs`. To resolve this:

1. Create a clean virtual environment
2. Install the exact versions of packages specified in requirements.txt
3. If issues persist, try the following workaround:
   ```bash
   # Install Node.js dependencies first (requires npm)
   npm init -y
   npm install constructs@10.3.0

   # Then install Python dependencies
   pip install -r requirements.txt
   ```

## Setup Steps

1. **Navigate to the CDK directory**:
   ```bash
   cd /Users/diegolima/Documents/projects/AIppointment/infrastructure/cdk
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies**:
   ```bash
   pip install pytest pytest-cov
   ```

5. **Install the CDK app in development mode**:
   ```bash
   pip install -e .
   ```

## Deployment Steps (Using AWS Profile "personal")

1. **Bootstrap the AWS environment** (if not already done):
   ```bash
   cdk bootstrap aws://<account-id>/<region> --profile personal
   ```

2. **Synthesize the CloudFormation template**:
   ```bash
   cdk synth --profile personal
   ```
   This will create a `cdk.out` directory with the CloudFormation templates.

3. **Deploy the CDK stack**:
   ```bash
   cdk deploy --profile personal
   ```

   For a specific environment:
   ```bash
   cdk deploy --context environment=dev --profile personal
   ```

4. **View the deployment progress** in the AWS CloudFormation console.

## Verification

After deployment, verify that the resources have been created correctly:

1. **Check that DynamoDB tables exist**:
   - `aippointment-appointments`
   - `aippointment-calendar-credentials`
   - `aippointment-conversation-history`
   - `aippointment-conversation-messages`

2. **Verify Lambda functions**:
   - `aippointment-booking`
   - `aippointment-appointment-creator`
   - `aippointment-appointment-manager`
   - `aippointment-calendar-integrator`

3. **Check the API Gateway**:
   - Endpoints should be available at the URL provided in the deployment output

4. **Verify the Bedrock Agent**:
   - Check that the agent is created in the Bedrock console
   - Verify that action groups are properly configured

## Troubleshooting

If you encounter issues with the CDK deployment:

1. **Check AWS credentials** - Ensure you're using the "personal" profile
2. **Verify Python dependencies** - Try reinstalling with exact versions
3. **Check CDK version compatibility** - The project is tested with CDK v2.103.0
4. **Examine CloudFormation errors** - Look for specific resource creation failures
