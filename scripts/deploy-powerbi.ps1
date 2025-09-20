param(
    [string]$WorkspaceId,
    [string]$PbixPath,
    [string]$ClientId,
    [string]$ClientSecret,
    [string]$TenantId
)

Write-Host "Authenticating to Power BI REST API..."
$body = @{
    grant_type    = "client_credentials"
    client_id     = $ClientId
    client_secret = $ClientSecret
    resource      = "https://analysis.windows.net/powerbi/api"
}

$tokenResponse = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$TenantId/oauth2/token" -Method Post -Body $body
$accessToken = $tokenResponse.access_token

if (-not $accessToken) {
    Write-Error "Failed to authenticate to Power BI API."
    exit 1
}

Write-Host "Uploading PBIX file to workspace..."
$headers = @{
    "Authorization" = "Bearer $accessToken"
}

# Fixed file upload method
$form = @{
    file = Get-Item -Path $PbixPath
}

$uri = "https://api.powerbi.com/v1.0/myorg/groups/$WorkspaceId/imports?datasetDisplayName=global_sales"

try {
    $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Post -Form $form
    Write-Host "PBIX file uploaded successfully."
    Write-Host "Import ID: $($response.id)"
}
catch {
    Write-Error "PBIX upload failed: $_"
    exit 1
}