$url = "http://127.0.0.1:8000/api/upload_fit"
# $fitFilePath = "E:\Shanghaitech\25Summer\Intervals\test\xxx.fit"
$fitFilePath = "E:\Shanghaitech\25Summer\Intervals\test\cp3_410w.fit"
# $fitFilePath = "E:\Shanghaitech\25Summer\Intervals\test\thp.fit"

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