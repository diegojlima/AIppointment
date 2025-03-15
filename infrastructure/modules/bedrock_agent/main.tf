# infrastructure/modules/bedrock_agent/main.tf

# Get current AWS region and account ID
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "schema_bucket" {
  bucket = "dijoseh-${var.project_name}-bedrock-schema-${var.environment}"

  tags = {
    Name        = "${var.project_name}-bedrock-schema"
    Environment = var.environment
  }
}

# Use local schema files to avoid path resolution issues in CI/CD
# Schema files are embedded in the module to avoid file path dependencies
resource "aws_s3_object" "appointment_creator_schema" {
  bucket       = aws_s3_bucket.schema_bucket.id
  key          = "appointment_creator_schema.json"
  content      = file("${path.module}/schema/action_groups/appointment_creator_schema.json")
  content_type = "application/json"
}

resource "aws_s3_object" "appointment_manager_schema" {
  bucket       = aws_s3_bucket.schema_bucket.id
  key          = "appointment_manager_schema.json"
  content      = file("${path.module}/schema/action_groups/appointment_manager_schema.json")
  content_type = "application/json"
}

resource "aws_s3_object" "calendar_integrator_schema" {
  bucket       = aws_s3_bucket.schema_bucket.id
  key          = "calendar_integrator_schema.json"
  content      = file("${path.module}/schema/action_groups/calendar_integrator_schema.json")
  content_type = "application/json"
}

# IAM Role for the Bedrock Agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-bedrock-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount": data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn": "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-bedrock-agent-role"
    Environment = var.environment
  }
}

# IAM Policy for the Bedrock Agent
resource "aws_iam_policy" "bedrock_agent_policy" {
  name        = "${var.project_name}-bedrock-agent-policy-${var.environment}"
  description = "Policy for Bedrock Agent to invoke Lambda functions, access S3, and invoke foundation models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "lambda:InvokeFunction"
        ]
        Effect   = "Allow"
        Resource = var.lambda_function_arns
      },
      {
        Action = [
          "s3:GetObject"
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.schema_bucket.arn}/*"
      },
      {
        Action = [
          "bedrock:InvokeModel"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        ]
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "bedrock_agent_policy_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_policy.arn
}

# Bedrock Agent
resource "aws_bedrockagent_agent" "appointment_agent" {
  agent_name              = "${var.project_name}-agent-${var.environment}"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn

  foundation_model = var.foundation_model
  instruction      = var.agent_instruction

  # Disable automatic preparation - we'll handle this manually
  prepare_agent = false
}

# Bedrock Agent Alias
resource "aws_bedrockagent_agent_alias" "agent_alias" {
  agent_id         = aws_bedrockagent_agent.appointment_agent.id
  agent_alias_name = var.environment
  description      = "${var.project_name} agent alias for ${var.environment} environment"
}

# Bedrock Agent Action Groups
resource "aws_bedrockagent_agent_action_group" "appointment_creator" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  agent_version     = "DRAFT"
  action_group_name = "AppointmentCreator"
  description       = "Creates appointments and checks availability"

  # Lambda function executor
  action_group_executor {
    lambda = var.appointment_creator_lambda_arn
  }

  # API Schema from S3
  api_schema {
    s3 {
      s3_bucket_name = aws_s3_bucket.schema_bucket.bucket
      s3_object_key  = aws_s3_object.appointment_creator_schema.key
    }
  }
}

resource "aws_bedrockagent_agent_action_group" "appointment_manager" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  agent_version     = "DRAFT"
  action_group_name = "AppointmentManager"
  description       = "Manages existing appointments (get, reschedule, cancel)"
  depends_on        = [aws_bedrockagent_agent_action_group.appointment_creator]

  # Lambda function executor
  action_group_executor {
    lambda = var.appointment_manager_lambda_arn
  }

  # API Schema from S3
  api_schema {
    s3 {
      s3_bucket_name = aws_s3_bucket.schema_bucket.bucket
      s3_object_key  = aws_s3_object.appointment_manager_schema.key
    }
  }
}

resource "aws_bedrockagent_agent_action_group" "calendar_integrator" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  agent_version     = "DRAFT"
  action_group_name = "CalendarIntegrator"
  description       = "Integrates with external calendar systems"
  depends_on        = [aws_bedrockagent_agent_action_group.appointment_manager]

  # Lambda function executor
  action_group_executor {
    lambda = var.calendar_integrator_lambda_arn
  }

  # API Schema from S3
  api_schema {
    s3 {
      s3_bucket_name = aws_s3_bucket.schema_bucket.bucket
      s3_object_key  = aws_s3_object.calendar_integrator_schema.key
    }
  }
}

# Add permissions for Bedrock to invoke Lambda functions
resource "aws_lambda_permission" "allow_bedrock_appointment_creator" {
  statement_id  = "AllowBedrockInvokeCreator"
  action        = "lambda:InvokeFunction"
  function_name = var.appointment_creator_lambda_arn
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
}

resource "aws_lambda_permission" "allow_bedrock_appointment_manager" {
  statement_id  = "AllowBedrockInvokeManager"
  action        = "lambda:InvokeFunction"
  function_name = var.appointment_manager_lambda_arn
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
}

resource "aws_lambda_permission" "allow_bedrock_calendar_integrator" {
  statement_id  = "AllowBedrockInvokeIntegrator"
  action        = "lambda:InvokeFunction"
  function_name = var.calendar_integrator_lambda_arn
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
}

# Manual agent preparation after all action groups are created
resource "null_resource" "prepare_agent" {
  depends_on = [
    aws_bedrockagent_agent.appointment_agent,
    aws_bedrockagent_agent_action_group.appointment_creator,
    aws_bedrockagent_agent_action_group.appointment_manager,
    aws_bedrockagent_agent_action_group.calendar_integrator,
    aws_lambda_permission.allow_bedrock_appointment_creator,
    aws_lambda_permission.allow_bedrock_appointment_manager,
    aws_lambda_permission.allow_bedrock_calendar_integrator
  ]
  
  provisioner "local-exec" {
    command = "aws bedrock-agent prepare-agent --agent-id ${aws_bedrockagent_agent.appointment_agent.id} --region ${data.aws_region.current.name}"
  }
}