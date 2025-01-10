terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
    telegram = {
      source = "yi-jiayu/telegram"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  cloud_id = var.cloud_id
  folder_id = var.folder_id
  service_account_key_file = "./key.json"
}

provider "telegram" {
  bot_token = var.TELEGRAM_BOT_TOKEN
}

resource "yandex_storage_bucket" "bucket" {
	bucket="vvot30"
}

resource "yandex_storage_object" "prompt" {
	bucket=yandex_storage_bucket.bucket.id
	key="prompt.json"
	source="./resources/prompt.json"
}

resource "yandex_function_iam_binding" "function-iam" {
  function_id = yandex_function.func.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}

resource "yandex_function" "func" {
  name = "tgbot-func"
  user_hash = archive_file.zip.output_sha256
  runtime = "python312"
  entrypoint = "index.handler"
  memory = 128
  execution_timeout  = "20"
  environment = {"TELEGRAM_BOT_TOKEN"= var.TELEGRAM_BOT_TOKEN, "SA_API_SECRET_KEY"=var.SA_API_SECRET_KEY, "SA_AWS_PUBLIC"=var.SA_AWS_PUBLIC, "SA_AWS_SECRET"=var.SA_AWS_SECRET, "BUCKET"="vvot30", "PROMPT_FILE"="prompt.json"}
  content {
    zip_filename = archive_file.zip.output_path
  }
}

resource "telegram_bot_webhook" "webhook" {
  url = "https://functions.yandexcloud.net/${yandex_function.func.id}"
}

variable "TELEGRAM_BOT_TOKEN" {
  type = string
}

variable "SA_API_SECRET_KEY" {
  type = string
}

variable "SA_AWS_PUBLIC" {
  type = string
}

variable "SA_AWS_SECRET" {
  type = string
}

variable "cloud_id" {
  type = string
}

variable "folder_id" {
  type = string
}

resource "archive_file" "zip" {
  type = "zip"
  output_path = "func.zip"
  source_dir = "./resources/tgbot_func"
}
