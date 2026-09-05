@echo off
setlocal EnableExtensions

cd /d "%~dp0"

title Compilar Convertidor de Archivos 1.1.1


REM ================================================================
REM CONFIGURACION
REM ================================================================

set "VERSION=1.1.1"
set "PYTHON=%CD%\.venv\Scripts\python.exe"
set "DIST=%CD%\dist\ConvertidorArchivos"


REM ================================================================
REM COMPROBAR ENTORNO
REM ================================================================

if not exist "%PYTHON%" (

    echo.
    echo ===============================================================
    echo.
    echo ERROR:
    echo No se encontro el entorno .venv.
    echo.
    echo Ruta esperada:
    echo %PYTHON%
    echo.
    echo ===============================================================
    echo.

    pause

    exit /b 1
)


REM ================================================================
REM COMPROBAR DEPENDENCIAS PYTHON
REM ================================================================

echo.
echo Comprobando dependencias Python...
echo.

"%PYTHON%" -c "import PySide6, PIL, pypdfium2, pypdf, openpyxl, pdfplumber, pikepdf, docx, lxml, numpy, onnxruntime, rembg; print('Dependencias principales: OK')"

if errorlevel 1 (

    echo.
    echo ===============================================================
    echo.
    echo ERROR:
    echo Faltan una o mas dependencias Python.
    echo.
    echo Puedes instalarlas con:
    echo.
    echo .venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-build.txt
    echo.
    echo ===============================================================
    echo.

    pause

    exit /b 1
)


REM ================================================================
REM COMPROBAR MOTOR PDF A DOCX
REM ================================================================

echo.
echo Comprobando motor PDF a DOCX...
echo.

"%PYTHON%" -c "from conversiones.pdf_docx import dependencias_pdf_docx_faltantes; f=dependencias_pdf_docx_faltantes(); print('Dependencias faltantes:', f); raise SystemExit(1 if f else 0)"

if errorlevel 1 (

    echo.
    echo ===============================================================
    echo.
    echo ERROR:
    echo El motor PDF a DOCX no tiene todas sus dependencias.
    echo.
    echo ===============================================================
    echo.

    pause

    exit /b 1
)


REM ================================================================
REM COMPROBAR REAL-ESRGAN
REM ================================================================

echo.
echo Comprobando Real-ESRGAN...
echo.

if not exist "%CD%\motores\realesrgan\realesrgan-ncnn-vulkan.exe" (
    goto ERROR_REALESRGAN
)

if not exist "%CD%\motores\realesrgan\models\realesrgan-x4plus.bin" (
    goto ERROR_REALESRGAN
)

if not exist "%CD%\motores\realesrgan\models\realesrgan-x4plus.param" (
    goto ERROR_REALESRGAN
)

if not exist "%CD%\motores\realesrgan\models\realesrgan-x4plus-anime.bin" (
    goto ERROR_REALESRGAN
)

if not exist "%CD%\motores\realesrgan\models\realesrgan-x4plus-anime.param" (
    goto ERROR_REALESRGAN
)


REM ================================================================
REM COMPROBAR MODELOS PARA QUITAR FONDO
REM ================================================================

echo.
echo Comprobando modelos de Quitar fondo...
echo.

if not exist "%CD%\motores\quitar_fondo\u2netp.onnx" (
    goto ERROR_QUITAR_FONDO
)

if not exist "%CD%\motores\quitar_fondo\isnet-general-use.onnx" (
    goto ERROR_QUITAR_FONDO
)

if not exist "%CD%\motores\quitar_fondo\birefnet-general.onnx" (
    goto ERROR_QUITAR_FONDO
)


REM ================================================================
REM LIMPIAR COMPILACIONES ANTERIORES
REM ================================================================

echo.
echo Limpiando compilaciones anteriores...
echo.

if exist "%CD%\build" (

    rmdir /s /q "%CD%\build"
)

if exist "%CD%\dist" (

    rmdir /s /q "%CD%\dist"
)


REM ================================================================
REM COMPILAR APLICACION
REM ================================================================

echo.
echo ===============================================================
echo.
echo Compilando Convertidor de Archivos %VERSION%...
echo.
echo ===============================================================
echo.

"%PYTHON%" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    "%CD%\ConvertidorArchivos.spec"

if errorlevel 1 (

    goto ERROR_COMPILACION
)


REM ================================================================
REM COMPROBAR RESULTADO
REM ================================================================

if not exist "%DIST%\ConvertidorArchivos.exe" (

    goto ERROR_COMPILACION
)


REM ================================================================
REM COPIAR MOTORES EXTERNOS
REM ================================================================

echo.
echo Copiando motores externos...
echo.

if exist "%CD%\motores" (

    xcopy ^
        "%CD%\motores" ^
        "%DIST%\motores\" ^
        /E /I /Y >nul

    if errorlevel 1 (

        goto ERROR_COPIA_MOTORES
    )
)


REM ================================================================
REM COPIAR LICENCIAS DE TERCEROS
REM ================================================================

if exist "%CD%\licencias_terceros" (

    echo.
    echo Copiando licencias de terceros...
    echo.

    xcopy ^
        "%CD%\licencias_terceros" ^
        "%DIST%\licencias_terceros\" ^
        /E /I /Y >nul

    if errorlevel 1 (

        goto ERROR_COPIA_LICENCIAS
    )
)


REM ================================================================
REM COPIAR ARCHIVOS INFORMATIVOS
REM ================================================================

if exist "%CD%\README.txt" (

    copy /Y ^
        "%CD%\README.txt" ^
        "%DIST%\README.txt" >nul
)

if exist "%CD%\LICENSE.txt" (

    copy /Y ^
        "%CD%\LICENSE.txt" ^
        "%DIST%\LICENSE.txt" >nul
)


REM ================================================================
REM COMPROBAR ARCHIVOS IMPORTANTES EN DIST
REM ================================================================

echo.
echo Comprobando archivos finales...
echo.

if not exist "%DIST%\motores\realesrgan\realesrgan-ncnn-vulkan.exe" (
    goto ERROR_VERIFICACION
)

if not exist "%DIST%\motores\quitar_fondo\u2netp.onnx" (
    goto ERROR_VERIFICACION
)

if not exist "%DIST%\motores\quitar_fondo\isnet-general-use.onnx" (
    goto ERROR_VERIFICACION
)

if not exist "%DIST%\motores\quitar_fondo\birefnet-general.onnx" (
    goto ERROR_VERIFICACION
)


REM ================================================================
REM CALCULAR TAMANO DE LA COMPILACION
REM ================================================================

echo.
echo Calculando tamano de la aplicacion compilada...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$b=(Get-ChildItem -LiteralPath '%DIST%' -Recurse -File | Measure-Object -Property Length -Sum).Sum; if($null -eq $b){$b=0}; if($b -ge 1GB){'{0:N2} GB' -f ($b/1GB)} elseif($b -ge 1MB){'{0:N2} MB' -f ($b/1MB)} elseif($b -ge 1KB){'{0:N2} KB' -f ($b/1KB)} else {'{0} B' -f $b}"


REM ================================================================
REM RESULTADO
REM ================================================================

echo.
echo ===============================================================
echo.
echo COMPILACION TERMINADA CORRECTAMENTE
echo.
echo Version:
echo %VERSION%
echo.
echo La aplicacion se encuentra en:
echo.
echo %DIST%
echo.
echo Ahora prueba el ejecutable:
echo.
echo %DIST%\ConvertidorArchivos.exe
echo.
echo Despues, si todo funciona:
echo.
echo 1. Abre instalador.iss con Inno Setup.
echo 2. Ve a Build.
echo 3. Pulsa Compile.
echo.
echo ===============================================================
echo.

explorer "%DIST%"

pause

exit /b 0


REM ================================================================
REM ERROR REAL-ESRGAN
REM ================================================================

:ERROR_REALESRGAN

echo.
echo ===============================================================
echo.
echo ERROR:
echo Falta Real-ESRGAN o alguno de sus modelos requeridos.
echo.
echo Revisa esta carpeta:
echo.
echo motores\realesrgan\
echo.
echo Deben existir como minimo:
echo.
echo realesrgan-ncnn-vulkan.exe
echo models\realesrgan-x4plus.bin
echo models\realesrgan-x4plus.param
echo models\realesrgan-x4plus-anime.bin
echo models\realesrgan-x4plus-anime.param
echo.
echo ===============================================================
echo.

pause

exit /b 1


REM ================================================================
REM ERROR QUITAR FONDO
REM ================================================================

:ERROR_QUITAR_FONDO

echo.
echo ===============================================================
echo.
echo ERROR:
echo Falta uno o mas modelos de Quitar fondo.
echo.
echo Revisa esta carpeta:
echo.
echo motores\quitar_fondo\
echo.
echo Deben existir:
echo.
echo u2netp.onnx
echo isnet-general-use.onnx
echo birefnet-general.onnx
echo.
echo ===============================================================
echo.

pause

exit /b 1


REM ================================================================
REM ERROR DE COMPILACION
REM ================================================================

:ERROR_COMPILACION

echo.
echo ===============================================================
echo.
echo ERROR AL COMPILAR
echo.
echo PyInstaller no pudo generar correctamente la aplicacion.
echo.
echo Revisa los mensajes mostrados anteriormente.
echo.
echo ===============================================================
echo.

pause

exit /b 1


REM ================================================================
REM ERROR AL COPIAR MOTORES
REM ================================================================

:ERROR_COPIA_MOTORES

echo.
echo ===============================================================
echo.
echo ERROR:
echo No fue posible copiar correctamente la carpeta motores.
echo.
echo ===============================================================
echo.

pause

exit /b 1


REM ================================================================
REM ERROR AL COPIAR LICENCIAS
REM ================================================================

:ERROR_COPIA_LICENCIAS

echo.
echo ===============================================================
echo.
echo ERROR:
echo No fue posible copiar correctamente licencias_terceros.
echo.
echo ===============================================================
echo.

pause

exit /b 1


REM ================================================================
REM ERROR DE VERIFICACION FINAL
REM ================================================================

:ERROR_VERIFICACION

echo.
echo ===============================================================
echo.
echo ERROR:
echo La compilacion termino, pero faltan archivos importantes en dist.
echo.
echo No generes todavia el instalador.
echo.
echo ===============================================================
echo.

pause

exit /b 1