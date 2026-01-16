Write-Host "🚀 COMMITTING FIXES TO GITHUB FIRST" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

# Check current status
Write-Host "`n1. Checking git status..." -ForegroundColor Yellow
git status

# Add all files
Write-Host "`n2. Adding all files..." -ForegroundColor Yellow
git add .

# Commit
Write-Host "`n3. Committing changes..." -ForegroundColor Yellow
git commit -m "FIX: Render deployment - Python 3.11.8 + SQLAlchemy 1.4.50 for compatibility"

# Push to GitHub
Write-Host "`n4. Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`n✅ COMMITTED TO GITHUB!" -ForegroundColor Green
Write-Host "`nNow go to Render:" -ForegroundColor Cyan
Write-Host "1. https://dashboard.render.com" -ForegroundColor White
Write-Host "2. Delete old failed service (if exists)" -ForegroundColor White
Write-Host "3. Create NEW web service" -ForegroundColor White
Write-Host "4. Select: ugbedethomas/pos-system" -ForegroundColor White
Write-Host "5. Configure or use Blueprint (render.yaml)" -ForegroundColor White

Write-Host "`n📋 Verify GitHub has latest code:" -ForegroundColor Cyan
Write-Host "https://github.com/ugbedethomas/pos-system" -ForegroundColor White
