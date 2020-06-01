# create zip archive locally
data "archive_file" "growing-load-spikes-monolith-function-code" {
  type = "zip"
  source_dir = "function_code/growing-load-spikes-monolith"
  output_path = "function1.zip"
}

# upload zip archive to storage contianer
resource "azurerm_storage_blob" "growing-load-spikes-monolith-code" {
  name = "growing-load-spikes-monolith-function.zip"
  storage_account_name = azurerm_storage_account.growing-load-spikes-experiment-storage.name
  storage_container_name = azurerm_storage_container.growing-load-spikes-container.name
  type = "Block"
  source = "function1.zip"
}

# create function app 'environment'
# different from how AWS lambda works
resource "azurerm_function_app" "growing-load-spikes-monolith" {
  depends_on = [azurerm_storage_blob.growing-load-spikes-monolith-code]

  name = "growing-load-spikes-function1"
  location = var.azure_region
  resource_group_name = azurerm_resource_group.growing-load-spikes-rg.name
  app_service_plan_id = azurerm_app_service_plan.growing-load-spikes-plan.id
  storage_connection_string = azurerm_storage_account.growing-load-spikes-experiment-storage.primary_connection_string
  version = "~2"

  app_settings = {
    HASH = data.archive_file.growing-load-spikes-monolith-function-code.output_base64sha256
    WEBSITE_RUN_FROM_PACKAGE = "${azurerm_storage_blob.growing-load-spikes-monolith-code.url}${data.azurerm_storage_account_sas.sas-growing-load-spikes.sas}"
    APPINSIGHTS_INSTRUMENTATIONKEY = azurerm_application_insights.growing-load-spikes.instrumentation_key
    FUNCTIONS_WORKER_RUNTIME = "python"
  }
}

# Get the functions key out of the app
resource "azurerm_template_deployment" "growing-load-spikes-monolith-function-key" {
  depends_on = [azurerm_function_app.growing-load-spikes-monolith]

  name = "growing-load-spikes-monolith_get_function_key"
  parameters = {
    "functionApp" = azurerm_function_app.growing-load-spikes-monolith.name
  }
  resource_group_name    = azurerm_resource_group.growing-load-spikes-rg.name
  deployment_mode = "Incremental"

  template_body = <<BODY
  {
      "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
      "contentVersion": "1.0.0.0",
      "parameters": {
          "functionApp": {"type": "string", "defaultValue": ""}
      },
      "variables": {
          "functionAppId": "[resourceId('Microsoft.Web/sites', parameters('functionApp'))]"
      },
      "resources": [
      ],
      "outputs": {
          "functionkey": {
              "type": "string",
              "value": "[listkeys(concat(variables('functionAppId'), '/host/default'), '2018-11-01').functionKeys.default]"                                                                                }
      }
  }
  BODY
}

# output some useful variables
output "growing-load-spikes-monolith_function_key" {
  value = "${lookup(azurerm_template_deployment.growing-load-spikes-monolith-function-key.outputs, "functionkey")}"
}
output "growing-load-spikes-monolith_function_app_url" {
  value = azurerm_function_app.growing-load-spikes-monolith.default_hostname
}
