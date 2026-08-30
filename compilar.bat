@echo off
setlocal

cd /d "%~dp0"

title Compilar Convertidor de Archivos


REM ================================================================
REM CONFIGURACION
REM ================================================================

set "PYTHON=%CD%\.venv_aspose_pdf\Scripts\python.exe"
set "DIST=%CD%\dist\ConvertidorArchivos"


REM ================================================================
REM COMPROBAR ENTORNO
REM ================================================================

if not exist "%PYTHON%" (
    echo.
    echo ERROR:
    echo No se encontro el entorno .venv_aspose_pdf.
    echo.
    pause
    exit /b 1
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
echo Compilando Convertidor de Archivos...
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
REM COPIAR MOTORES PRIVADOS
REM ================================================================

echo.
echo Copiando motores...
echo.

if exist "%CD%\motores" (
    xcopy ^
        "%CD%\motores" ^
        "%DIST%\motores\" ^
        /E /I /Y >nul
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
REM RESULTADO
REM ================================================================

echo.
echo ===============================================================
echo.
echo COMPILACION TERMINADA
echo.
echo Convertidor de Archivos 1.0 se encuentra en:
echo.
echo %DIST%
echo.
echo ===============================================================
echo.

explorer "%DIST%"

pause
exit /b 0


REM ================================================================
REM ERROR
REM ================================================================

:ERROR_COMPILACION

echo.
echo ===============================================================
echo.
echo ERROR AL COMPILAR
echo.
echo Revisa los mensajes mostrados por PyInstaller.
echo.
echo ===============================================================
echo.

pause
exit /b 1