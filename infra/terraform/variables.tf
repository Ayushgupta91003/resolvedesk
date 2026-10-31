variable "region" {
  type    = string
  default = "ap-south-1"
}
variable "name" {
  type    = string
  default = "resolvedesk"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.name))
    error_message = "Use 3–20 lowercase letters, digits or hyphens, starting with a letter."
  }
}
variable "certificate_arn" {
  type        = string
  description = "An issued ACM certificate in the deployment region. HTTPS is required."
}
variable "app_origin" {
  type        = string
  description = "Exact HTTPS origin, e.g. https://support.example.com. Point its DNS to the ALB."
  validation {
    condition     = can(regex("^https://[^/]+$", var.app_origin))
    error_message = "Provide an HTTPS origin without a trailing slash or path."
  }
}
variable "image_tag" {
  type    = string
  default = "latest"
}
variable "desired_count" {
  type        = number
  default     = 0
  description = "First apply with 0, push images, then set 1. Single-worker MVP only."
  validation {
    condition     = contains([0, 1], var.desired_count)
    error_message = "This MVP supports a single API worker only."
  }
}
variable "agent_mode" {
  type    = string
  default = "demo"
  validation {
    condition     = contains(["demo", "llm"], var.agent_mode)
    error_message = "Use demo or llm."
  }
}
variable "openai_secret_arn" {
  type        = string
  default     = ""
  description = "Optional existing Secrets Manager secret containing only the OpenAI API key."
}
variable "openai_model" {
  type    = string
  default = "gpt-4.1-mini"
}
