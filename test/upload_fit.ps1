# $url = "http://121.41.238.53:8000/api/upload_fit"
$url = "http://localhost:8000/api/upload_fit"
# $fitFilePath = ".\Fits\19501148013_ACTIVITY.fit"
# $fitFilePath = ".\Fits\19300542613_ACTIVITY.fit"
# $fitFilePath = ".\Fits\19410463815_ACTIVITY.fit"
# $fitFilePath = ".\Fits\19449462560_ACTIVITY.fit"
$fitFilePath = ".\Fits\Zwift_Road_to_Sky_in_Watopia.fit"
# $fitFilePath = ".\Fits\cp3_410w.fit"

if (-Not (Test-Path $fitFilePath)) {
    Write-Host "错误：找不到 FIT 文件路径 $fitFilePath"
    exit 1
}


$form = @{
    file = Get-Item -Path $fitFilePath
}


try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Form $form
    Write-Host "`n✅ 上传成功，收到服务器响应："
    $response | ConvertTo-Json -Depth 3
}
catch {
    Write-Host "`n❌ 请求失败："
    Write-Host $_.Exception.Message
}