# update_user_config.ps1

$URL = "http://127.0.0.1:8000/api/user_config"

$json = @'
{
  "weight": 62.5,
  "power": {
    "FTP": 272
  },
  "heart_rate": {
    "max_bpm": 208
  }
}
'@

Invoke-RestMethod -Method Patch -Uri "$URL" `
  -Body $json `
  -ContentType "application/json"
