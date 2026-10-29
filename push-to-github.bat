@echo off
title Craft Apps for iPad - GitHub Builder Setup
echo ========================================================
echo   PhotoCraft, WordCraft, and PdfCraft for iPadOS (M1)
echo ========================================================
echo.
echo Step 1: Go to https://github.com/new in your browser
echo Step 2: Type a repository name (for example: craft-ipad-apps)
echo Step 3: Choose "Private" (or "Public") and click "Create repository"
echo Step 4: Copy the repository URL (e.g. https://github.com/YOUR-NAME/craft-ipad-apps.git)
echo.
set /p REPO_URL="Paste your GitHub repository URL here and press Enter: "

if "%REPO_URL%"=="" (
    echo No URL entered. Exiting.
    pause
    exit /b 1
)

git remote remove origin 2>nul
git remote add origin "%REPO_URL%"
git branch -M main
echo.
echo Uploading your iPad Wrapper project to GitHub...
git push -u origin main

echo.
echo ========================================================
echo Done! Now open your GitHub repository in your browser,
echo click the "Actions" tab at the top, and wait for the
echo build to finish. At the bottom of the finished run,
echo download:
echo   - PhotoCraft-iPad-IPA
echo   - WordCraft-iPad-IPA
echo   - PdfCraft-iPad-IPA
echo ========================================================
pause
