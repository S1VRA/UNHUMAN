@echo off
echo ==========================================
echo   NH Mod Tool - Nuitka Build v0.5.0
echo ==========================================
echo.

REM Eski build artıklarını temizle
if exist dist\NHModTool rmdir /s /q dist\NHModTool
if exist build rmdir /s /q build
if exist NHModTool.build rmdir /s /q NHModTool.build
if exist NHModTool.dist rmdir /s /q NHModTool.dist

echo [1/2] Nuitka ile derleniyor... (5-10 dakika sürebilir)
REM astc_encoder haric tutuluyor: oyunda ASTC texture yok (RGBA32/DXT5).
REM --nofollow-import-to tek basina yetmez, top-level import satiri kodda kalir ve
REM AVX2 olmayan CPU'da ImportError verir. astc_exclude.yml o satiri siler.
python -m nuitka ^
  --standalone ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --include-package=ttkbootstrap ^
  --include-package-data=ttkbootstrap ^
  --include-package=UnityPy ^
  --include-package-data=UnityPy ^
  --nofollow-import-to=astc_encoder ^
  --user-package-configuration-file=astc_exclude.yml ^
  --include-package=fmod_toolkit ^
  --include-package-data=fmod_toolkit ^
  --include-package=PIL ^
  --include-package-data=PIL ^
  --include-package=numpy ^
  --include-package-data=numpy ^
  --include-package=archspec ^
  --include-package-data=archspec ^
  --include-data-dir="C:\Users\mehmet\AppData\Roaming\Python\Python314\site-packages\archspec"="archspec" ^
  --include-data-files="C:\Users\mehmet\AppData\Roaming\Python\Python314\site-packages\fmod_toolkit\libfmod\Windows\x64\fmod.dll"="fmod_toolkit/libfmod/Windows/x64/fmod.dll" ^
  --windows-icon-from-ico=NHModTool.ico ^
  --windows-company-name=S1VRA ^
  --windows-product-name="NH Mod Tool" ^
  --windows-file-version=0.5.0.0 ^
  --windows-product-version=0.5.0.0 ^
  --include-data-dir=locales=locales ^
  --output-dir=dist ^
  --output-filename=NHModTool.exe ^
  --assume-yes-for-downloads ^
  NHModTool.py

if not exist "dist\NHModTool.dist\NHModTool.exe" (
    echo.
    echo [HATA] Build başarısız - EXE oluşmadı!
    pause
    exit /b 1
)

echo.
echo [2/2] SHA-256 hash üretiliyor...
powershell -Command "Get-FileHash 'dist\NHModTool.dist\NHModTool.exe' -Algorithm SHA256 | Out-File -Encoding utf8 dist\SHA256SUMS.txt"

echo.
echo ==========================================
echo   BUILD BAŞARILI
echo ==========================================
echo EXE konumu: dist\NHModTool.dist\NHModTool.exe
echo Hash: dist\SHA256SUMS.txt
echo.
pause