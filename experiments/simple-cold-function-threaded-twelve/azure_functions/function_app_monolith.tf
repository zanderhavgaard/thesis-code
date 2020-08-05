# create function app 'environment'
# different from how AWS lambda works
resource "azurerm_function_app" "simple-cold-function-threaded-twelve-monolith" {

  name = "simple-cold-function-threaded-twelve-monolith"
  location = var.azure_region
  resource_group_name = azurerm_resource_group.simple-cold-function-threaded-twelve-rg.name
  app_service_plan_id = azurerm_app_service_plan.simple-cold-function-threaded-twelve-plan.id
  storage_connection_string = azurerm_storage_account.simple-cold-function-threaded-twelve-experiment-storage.primary_connection_string
  version = "~2"

  app_settings = {
    APPINSIGHTS_INSTRUMENTATIONKEY = azurerm_application_insights.simple-cold-function-threaded-twelve.instrumentation_key
    FUNCTIONS_WORKER_RUNTIME = "python"
  }
}

# Get the functions key out of the app
resource "azurerm_template_deployment" "simple-cold-function-threaded-twelve-monolith-function-key" {
  depends_on = [azurerm_function_app.simple-cold-function-threaded-twelve-monolith]

  name = "simple-cold-function-threaded-twelve-monolith_get_function_key"
  parameters = {
    "functionApp" = azurerm_function_app.simple-cold-function-threaded-twelve-monolith.name
  }
  resource_group_name    = azurerm_resource_group.simple-cold-function-threaded-twelve-rg.name
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
output "simple-cold-function-threaded-twelve-monolith_function_key" {
  value = "${lookup(azurerm_template_deployment.simple-cold-function-threaded-twelve-monolith-function-key.outputs, "functionkey")}"
}
output "simple-cold-function-threaded-twelve-monolith_function_app_url" {
  value = azurerm_function_app.simple-cold-function-threaded-twelve-monolith.default_hostname
}