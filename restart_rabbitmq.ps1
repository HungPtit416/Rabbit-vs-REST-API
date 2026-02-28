# Script để restart RabbitMQ với cấu hình tối ưu cho high load

Write-Host "=" -NoNewline -ForegroundColor Cyan; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "RESTART RABBITMQ VỚI CẤU HÌNH TỐI ƯU" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan; Write-Host ("=" * 59) -ForegroundColor Cyan

# Dừng và xóa container cũ
Write-Host "`n1. Dừng RabbitMQ container cũ..." -ForegroundColor Yellow
docker stop rabbitmq 2>$null
docker rm rabbitmq 2>$null

Start-Sleep -Seconds 2

# Tạo container mới với cấu hình cao hơn
Write-Host "`n2. Khởi tạo RabbitMQ với cấu hình mới..." -ForegroundColor Yellow
docker run -d --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_VM_MEMORY_HIGH_WATERMARK=1024MiB `
  -e RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="+P 1048576" `
  rabbitmq:3-management

Write-Host "`n3. Đợi RabbitMQ khởi động..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Tăng connection limits
Write-Host "`n4. Tăng connection limits..." -ForegroundColor Yellow
docker exec rabbitmq rabbitmqctl set_vm_memory_high_watermark 0.8

Write-Host "`nHOÀN TẤT!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "`nRabbitMQ Management UI: http://localhost:15672" -ForegroundColor Cyan
Write-Host "   Username: guest" -ForegroundColor White
Write-Host "   Password: guest" -ForegroundColor White
Write-Host "`nCấu hình:" -ForegroundColor Cyan
Write-Host "   - Max memory: 1024MB" -ForegroundColor White
Write-Host "   - Max processes: 1,048,576" -ForegroundColor White
Write-Host "   - Memory watermark: 80%" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan; Write-Host ("=" * 59) -ForegroundColor Cyan
