# create function app 'environment'
# different from how AWS lambda works
resource "azurerm_function_app" "linear-invocation-nested3" {

  name = "linear-invocation-nested-function3"
  location = var.azure_region
  resource_group_name = azurerm_resource_group.linear-invocation-nested-rg.name
  app_service_plan_id = azurerm_app_service_plan.linear-invocation-nested-plan.id
  storage_connection_string = azurerm_storage_account.linear-invocation-nested-experiment-storage.primary_connection_string
  version = "~2"

  app_settings = {
    APPINSIGHTS_INSTRUMENTATIONKEY = azurerm_application_insights.linear-invocation-nested.instrumentation_key
    FUNCTIONS_WORKER_RUNTIME = "python"
  }
}

# Get the functions key out of the app
resource "azurerm_template_deployment" "linear-invocation-nested3-function-key" {
  depends_on = [azurerm_function_app.linear-invocation-nested3]

  name = "linear-invocation-nested3_get_function_key"
  parameters = {
    "functionApp" = azurerm_function_app.linear-invocation-nested3.name
  }
  resource_group_name    = azurerm_resource_group.linear-invocation-nested-rg.name
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
output "linear-invocation-nested-function3_function_key" {
  value = "${lookup(azurerm_template_deployment.linear-invocation-nested3-function-key.outputs, "functionkey")}"
}
output "linear-invocation-nested-function3_function_app_url" {
  value = azurerm_function_app.linear-invocation-nested3.default_hostname
}
