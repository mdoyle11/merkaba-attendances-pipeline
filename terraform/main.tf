terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ------------------------------------------------------------------------------
# 1. Artifact Registry (Docker Repository)
# ------------------------------------------------------------------------------
resource "google_artifact_registry_repository" "etl_repo" {
  location      = var.gcp_region
  repository_id = "attendance-etl-repo"
  description   = "Docker repository for Attendance ETL container"
  format        = "DOCKER"
}

# ------------------------------------------------------------------------------
# 2. Secret Manager Resources
# ------------------------------------------------------------------------------
resource "google_secret_manager_secret" "m2m_token" {
  secret_id = "teamup-m2m-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "sheet_id" {
  secret_id = "google-sheet-id"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "app_password" {
  secret_id = "email-app-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gspread_creds" {
  secret_id = "gspread-credentials-json"
  replication {
    auto {}
  }
}

# ------------------------------------------------------------------------------
# 3. IAM & Service Account for Cloud Run
# ------------------------------------------------------------------------------
resource "google_service_account" "etl_runner" {
  account_id   = "attendance-etl-runner"
  display_name = "Attendance ETL Cloud Run Service Account"
}

# Grant Service Account access to Secret Manager Secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = {
    m2m_token     = google_secret_manager_secret.m2m_token.secret_id
    sheet_id      = google_secret_manager_secret.sheet_id.secret_id
    app_password  = google_secret_manager_secret.app_password.secret_id
    gspread_creds = google_secret_manager_secret.gspread_creds.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.etl_runner.email}"
}

resource "google_project_iam_member" "etl_runner_logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# ------------------------------------------------------------------------------
# 4. Cloud Run Job
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_job" "etl_job" {
  name     = "attendance-etl-job"
  location = var.gcp_region

  template {
    template {
      service_account = google_service_account.etl_runner.email
      timeout         = "600s" # 10 minute execution limit

      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.etl_repo.repository_id}/teamup-etl:latest"

        # Non-sensitive environment variables
        env {
          name  = "SENDER_EMAIL"
          value = var.sender_email
        }
        env {
          name  = "RECIPIENT_EMAIL"
          value = var.recipient_email
        }

        # Inject Secrets as Environment Variables
        env {
          name = "M2M_TOKEN"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.m2m_token.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "SHEET_ID"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.sheet_id.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "APP_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app_password.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "GSPREAD_CREDENTIALS_JSON"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.gspread_creds.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.secret_access]
}

# ------------------------------------------------------------------------------
# 5. Cloud Scheduler (Weekly Execution)
# ------------------------------------------------------------------------------
resource "google_service_account" "scheduler_sa" {
  account_id   = "attendance-etl-scheduler"
  display_name = "Cloud Scheduler Invoker Service Account"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  location = google_cloud_run_v2_job.etl_job.location
  name     = google_cloud_run_v2_job.etl_job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_cloud_scheduler_job" "weekly_trigger" {
  name             = "weekly-attendance-sync"
  description      = "Triggers Attendance ETL pipeline every Monday at 06:00 AM"
  schedule         = "0 6 * * 1"
  time_zone        = var.time_zone
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.gcp_region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.gcp_project_id}/jobs/${google_cloud_run_v2_job.etl_job.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}

# ------------------------------------------------------------------------------
# 6. Monitoring Alerting Policy (Pipeline Failure Alert)
# ------------------------------------------------------------------------------
resource "google_monitoring_notification_channel" "email_alert" {
  display_name = "ETL Failure Notification"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "job_failure_alert" {
  display_name = "Attendance ETL Job Execution Failure"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Job Failure"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_job\" AND resource.labels.job_name = \"${google_cloud_run_v2_job.etl_job.name}\" AND metric.type = \"run.googleapis.com/job/completed_execution_count\" AND metric.labels.result = \"failed\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email_alert.name]
}