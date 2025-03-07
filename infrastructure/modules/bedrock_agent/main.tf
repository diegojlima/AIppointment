# infrastructure/modules/bedrock_agent/main.tf

resource "aws_s3_bucket" "schema_bucket" {
  bucket = "${var.project_name}-bedrock-schema-${var.environment}"
  
  tags = {
    Name        = "${var.project_name}-bedrock-schema"
    Environment = var.environment
  }
}

resource "aws_s3_object" "schema_object" {
  bucket = aws_s3_bucket.schema_bucket.id
  key    = "agent_schema.json"
  source = var.schema_path
  etag   = filemd5(var.schema_path)
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
  description = "Policy for Bedrock Agent to invoke Lambda functions and access S3"

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
  
  foundation_model = var.foundation_model_id
  instruction      = var.agent_instruction
}

# Bedrock Agent API Schema
resource "aws_bedrockagent_agent_api_schema" "appointment_schema" {
  agent_id      = aws_bedrockagent_agent.appointment_agent.id
  agent_version = "DRAFT"
  
  s3_data_source {
    bucket_name = aws_s3_bucket.schema_bucket.bucket
    object_key  = aws_s3_object.schema_object.key
  }
}

# Bedrock Agent Alias
resource "aws_bedrockagent_agent_alias" "agent_alias" {
  agent_id    = aws_bedrockagent_agent.appointment_agent.id
  alias_name  = var.environment
  description = "${var.project_name} agent alias for ${var.environment} environment"
}

# Bedrock Agent Action Groups
resource "aws_bedrockagent_agent_action_group" "appointment_creator" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  action_group_name = "AppointmentCreator"
  description       = "Creates appointments and checks availability"
  
  action_group_executor {
    lambda {
      lambda_arn = var.appointment_creator_lambda_arn
    }
  }
}

resource "aws_bedrockagent_agent_action_group" "appointment_manager" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  action_group_name = "AppointmentManager"
  description       = "Manages existing appointments (get, reschedule, cancel)"
  
  action_group_executor {
    lambda {
      lambda_arn = var.appointment_manager_lambda_arn
    }
  }
}

resource "aws_bedrockagent_agent_action_group" "calendar_integrator" {
  agent_id          = aws_bedrockagent_agent.appointment_agent.id
  action_group_name = "CalendarIntegrator"
  description       = "Integrates with external calendar systems"
  
  action_group_executor {
    lambda {
      lambda_arn = var.calendar_integrator_lambda_arn
    }
  }
}