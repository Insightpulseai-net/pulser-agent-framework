# DigitalOcean Infrastructure for InsightPulseAI AI Workbench
# Terraform v1.0+
# Provider: digitalocean v2.34+

terraform {
  required_version = ">= 1.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.34"
    }
  }

  backend "s3" {
    # Use DigitalOcean Spaces for state storage
    endpoint                    = "sgp1.digitaloceanspaces.com"
    region                      = "us-east-1" # Dummy region for S3 compatibility
    bucket                      = "ai-workbench-terraform-state"
    key                         = "production/terraform.tfstate"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
  }
}

provider "digitalocean" {
  token = var.do_token
}

# Variables
variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ai-workbench"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "sgp1"
}

variable "environment" {
  description = "Environment (production/staging)"
  type        = string
  default     = "production"
}

# VPC for private networking
resource "digitalocean_vpc" "workbench_vpc" {
  name     = "${var.project_name}-vpc-${var.environment}"
  region   = var.region
  ip_range = "10.10.0.0/16"

  description = "Private network for AI Workbench services"
}

# DOKS (DigitalOcean Kubernetes Service) Cluster
resource "digitalocean_kubernetes_cluster" "workbench_cluster" {
  name    = "${var.project_name}-cluster-${var.environment}"
  region  = var.region
  version = "1.29.4-do.0" # Update to latest stable
  vpc_uuid = digitalocean_vpc.workbench_vpc.id

  auto_upgrade = true
  surge_upgrade = true
  ha           = false # Enable for production HA

  maintenance_policy {
    start_time = "04:00"
    day        = "sunday"
  }

  node_pool {
    name       = "worker-pool"
    size       = "s-4vcpu-8gb" # 4 vCPU, 8GB RAM
    node_count = 3
    auto_scale = true
    min_nodes  = 3
    max_nodes  = 6

    tags = ["${var.project_name}", "${var.environment}", "worker"]

    labels = {
      environment = var.environment
      role        = "worker"
    }
  }

  tags = ["${var.project_name}", "${var.environment}"]
}

# Firewall for DOKS cluster
resource "digitalocean_firewall" "workbench_firewall" {
  name = "${var.project_name}-firewall-${var.environment}"
  tags = [digitalocean_kubernetes_cluster.workbench_cluster.node_pool[0].nodes[0].tags[0]]

  # Inbound rules
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow internal cluster communication
  inbound_rule {
    protocol         = "tcp"
    port_range       = "all"
    source_tags      = ["${var.project_name}"]
  }

  inbound_rule {
    protocol         = "udp"
    port_range       = "all"
    source_tags      = ["${var.project_name}"]
  }

  # Outbound rules
  outbound_rule {
    protocol              = "tcp"
    port_range            = "443"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "5432" # PostgreSQL (Supabase)
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "6543" # Supabase Pooler
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "6333" # Qdrant
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "80"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "53" # DNS
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# App Platform Specs (OCR Backend, Expense API)
resource "digitalocean_app" "ocr_backend" {
  spec {
    name   = "${var.project_name}-ocr-backend"
    region = var.region

    service {
      name               = "ocr-backend"
      instance_count     = 2
      instance_size_slug = "professional-xs" # 1 vCPU, 2GB RAM

      git {
        repo_clone_url = "https://github.com/insightpulseai/ai-workbench.git"
        branch         = "main"
      }

      dockerfile_path = "services/ocr-backend/Dockerfile"

      http_port = 8080

      routes {
        path = "/"
      }

      health_check {
        http_path             = "/health"
        initial_delay_seconds = 10
        period_seconds        = 10
        timeout_seconds       = 5
        success_threshold     = 1
        failure_threshold     = 3
      }

      env {
        key   = "MODEL"
        value = "paddleocr-vl-900m"
      }

      env {
        key   = "MIN_CONFIDENCE"
        value = "0.60"
      }
    }
  }
}

resource "digitalocean_app" "expense_api" {
  spec {
    name   = "${var.project_name}-expense-api"
    region = var.region

    service {
      name               = "expense-api"
      instance_count     = 2
      instance_size_slug = "professional-xs"

      git {
        repo_clone_url = "https://github.com/insightpulseai/ai-workbench.git"
        branch         = "main"
      }

      dockerfile_path = "services/expense-api/Dockerfile"

      http_port = 8000

      routes {
        path = "/"
      }

      health_check {
        http_path             = "/health"
        initial_delay_seconds = 10
        period_seconds        = 10
        timeout_seconds       = 5
        success_threshold     = 1
        failure_threshold     = 3
      }

      env {
        key   = "SUPABASE_URL"
        value = var.supabase_url
        type  = "SECRET"
      }

      env {
        key   = "SUPABASE_SERVICE_ROLE_KEY"
        value = var.supabase_service_role_key
        type  = "SECRET"
      }
    }
  }
}

# Spaces bucket for assets (optional)
resource "digitalocean_spaces_bucket" "workbench_assets" {
  name   = "${var.project_name}-assets-${var.environment}"
  region = var.region
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "delete-old-versions"
    enabled = true

    noncurrent_version_expiration {
      days = 90
    }
  }
}

# Container Registry
resource "digitalocean_container_registry" "workbench_registry" {
  name                   = "${var.project_name}-registry"
  subscription_tier_slug = "basic" # 5 repos, 500MB storage
  region                 = var.region
}

# Outputs
output "cluster_id" {
  description = "DOKS cluster ID"
  value       = digitalocean_kubernetes_cluster.workbench_cluster.id
}

output "cluster_endpoint" {
  description = "DOKS cluster API endpoint"
  value       = digitalocean_kubernetes_cluster.workbench_cluster.endpoint
}

output "cluster_kubeconfig" {
  description = "DOKS kubeconfig"
  value       = digitalocean_kubernetes_cluster.workbench_cluster.kube_config[0].raw_config
  sensitive   = true
}

output "vpc_id" {
  description = "VPC UUID"
  value       = digitalocean_vpc.workbench_vpc.id
}

output "ocr_backend_url" {
  description = "OCR Backend URL"
  value       = digitalocean_app.ocr_backend.live_url
}

output "expense_api_url" {
  description = "Expense API URL"
  value       = digitalocean_app.expense_api.live_url
}

output "spaces_bucket_name" {
  description = "Spaces bucket name"
  value       = digitalocean_spaces_bucket.workbench_assets.name
}

output "container_registry_endpoint" {
  description = "Container registry endpoint"
  value       = digitalocean_container_registry.workbench_registry.endpoint
}

# Additional variables for App Platform
variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
  sensitive   = true
}

variable "supabase_service_role_key" {
  description = "Supabase service role key"
  type        = string
  sensitive   = true
}
