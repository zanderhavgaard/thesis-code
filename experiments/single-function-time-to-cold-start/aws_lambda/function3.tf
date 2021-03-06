
# creates zip archive containing lambda code
data "archive_file" "single-function-time-to-cold-start3-lambda-code" {
  type = "zip"
  source_file = "${var.path_to_code}/function3.py"
  output_path = "${var.path_to_code}/lambda3.zip"
}

# create API endpoint
resource "aws_api_gateway_resource" "single-function-time-to-cold-start3-api-resource" {
  rest_api_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.id
  parent_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.root_resource_id
  path_part = aws_lambda_function.single-function-time-to-cold-start3-python.function_name
}

# create API endpoint method
resource "aws_api_gateway_method" "single-function-time-to-cold-start3-lambda-method" {
  rest_api_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.id
  resource_id = aws_api_gateway_resource.single-function-time-to-cold-start3-api-resource.id
  http_method = "POST"
  authorization = "None"
  api_key_required = true
}

resource "aws_api_gateway_method_response" "single-function-time-to-cold-start2-response_200" {
  rest_api_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.id
  resource_id = aws_api_gateway_resource.single-function-time-to-cold-start3-api-resource.id
  http_method = aws_api_gateway_method.single-function-time-to-cold-start3-lambda-method.http_method
  status_code = "200"
}

# point API endpoint at lambda function
resource "aws_api_gateway_integration" "single-function-time-to-cold-start3-api-integration" {
  rest_api_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.id
  resource_id = aws_api_gateway_method.single-function-time-to-cold-start3-lambda-method.resource_id
  http_method = aws_api_gateway_method.single-function-time-to-cold-start3-lambda-method.http_method
  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.single-function-time-to-cold-start3-python.invoke_arn
}

resource "aws_api_gateway_integration_response" "single-function-time-to-cold-start3" {
  depends_on = [
    aws_api_gateway_integration.single-function-time-to-cold-start3-api-integration
  ]
  rest_api_id = aws_api_gateway_rest_api.single-function-time-to-cold-start-api.id
  resource_id = aws_api_gateway_method.single-function-time-to-cold-start3-lambda-method.resource_id
  http_method = aws_api_gateway_method.single-function-time-to-cold-start3-lambda-method.http_method
  status_code = aws_api_gateway_method_response.single-function-time-to-cold-start2-response_200.status_code
}

# add permission for gateway to invoke lambdas
resource "aws_lambda_permission" "single-function-time-to-cold-start3-apigw-permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.single-function-time-to-cold-start3-python.function_name
  principal     = "apigateway.amazonaws.com"

  # The "/*/*" portion grants access from any method on any resource
  # within the API Gateway REST API.
  source_arn = "${aws_api_gateway_rest_api.single-function-time-to-cold-start-api.execution_arn}/*/*"
}

# create lambda function
resource "aws_lambda_function" "single-function-time-to-cold-start3-python" {
  filename = data.archive_file.single-function-time-to-cold-start3-lambda-code.output_path
  function_name = "single-function-time-to-cold-start-function3"
  role = aws_iam_role.single-function-time-to-cold-start-role.arn
  handler = "function3.lambda_handler"
  runtime = "python3.7"
  source_code_hash = filesha256(data.archive_file.single-function-time-to-cold-start3-lambda-code.output_path)
  publish = true
  layers = [aws_lambda_layer_version.single-function-time-to-cold-start-lambda-layer.arn]
  timeout = 60
}
