$ErrorActionPreference = "Stop"

$carpetaProyecto = Split-Path -Parent $MyInvocation.MyCommand.Path
$carpetaLicencias = Join-Path $carpetaProyecto "licencias_terceros"

New-Item -ItemType Directory -Force -Path $carpetaLicencias | Out-Null


# ================================================================
# LICENCIAS NUEVAS DE LA VERSION 1.1.1
# ================================================================

$archivos = @(
    @{
        Nombre = "Real-ESRGAN_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/xinntao/Real-ESRGAN/master/LICENSE"
    },
    @{
        Nombre = "ncnn_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/Tencent/ncnn/master/LICENSE.txt"
    },
    @{
        Nombre = "rembg_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/danielgatis/rembg/main/LICENSE.txt"
    },
    @{
        Nombre = "ONNX_Runtime_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/microsoft/onnxruntime/main/LICENSE"
    },
    @{
        Nombre = "ONNX_Runtime_ThirdPartyNotices.txt"
        Url = "https://raw.githubusercontent.com/microsoft/onnxruntime/main/ThirdPartyNotices.txt"
    },
    @{
        Nombre = "U2Net_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/xuebinqin/U-2-Net/master/LICENSE"
    },
    @{
        Nombre = "DIS_ISNet_LICENSE.txt"
        Url = "https://www.apache.org/licenses/LICENSE-2.0.txt"
    },
    @{
        Nombre = "BiRefNet_LICENSE.txt"
        Url = "https://raw.githubusercontent.com/ZhengPeng7/BiRefNet/main/LICENSE"
    }
)


Write-Host ""
Write-Host "Preparando licencias de terceros para v1.1.1..."
Write-Host ""

foreach ($archivo in $archivos) {

    $destino = Join-Path $carpetaLicencias $archivo.Nombre

    Write-Host "Descargando $($archivo.Nombre)..."

    Invoke-WebRequest `
        -Uri $archivo.Url `
        -OutFile $destino `
        -UseBasicParsing
}


# ================================================================
# NOTA DE PROCEDENCIA DE MODELOS
# ================================================================

$nota = @"
MODELOS DE IA INCLUIDOS EN CONVERTIDOR DE ARCHIVOS 1.1.1
========================================================

Esta aplicación incluye modelos locales para funciones de procesamiento
de imágenes. Los proyectos originales y sus licencias se documentan en
esta misma carpeta.

MEJORAR CALIDAD
---------------

Real-ESRGAN
Proyecto:
https://github.com/xinntao/Real-ESRGAN

Motor NCNN/Vulkan:
https://github.com/Tencent/ncnn


QUITAR FONDO
------------

U²-NetP
Proyecto original:
https://github.com/xuebinqin/U-2-Net

IS-Net General Use
Proyecto original DIS:
https://github.com/xuebinqin/DIS

BiRefNet General
Proyecto original:
https://github.com/ZhengPeng7/BiRefNet

La ejecución ONNX se realiza mediante:
https://github.com/microsoft/onnxruntime

La integración de eliminación de fondo utiliza:
https://github.com/danielgatis/rembg


NOTA
----

Los archivos ONNX utilizados por la aplicación son conversiones o
distribuciones compatibles con los modelos anteriores. Las licencias de
los proyectos originales y de los motores de ejecución se incluyen por
separado en esta carpeta.

Este archivo es únicamente informativo y no sustituye los textos de
licencia originales.
"@

$rutaNota = Join-Path $carpetaLicencias "MODELOS_IA_PROCEDENCIA.txt"

Set-Content `
    -Path $rutaNota `
    -Value $nota `
    -Encoding UTF8


Write-Host ""
Write-Host "Licencias preparadas en:"
Write-Host $carpetaLicencias
Write-Host ""