; ================================================================
; CONVERTIDOR DE ARCHIVOS 1.1.0
; INSTALADOR OFICIAL
; ================================================================


#define NombreAplicacion "Convertidor de Archivos"
#define VersionAplicacion "1.1.0"
#define EjecutableAplicacion "ConvertidorArchivos.exe"
#define CarpetaCompilada "dist\ConvertidorArchivos"
#define NombreInstalador "ConvertidorArchivos_Setup_1.1.0"


; ================================================================
; CONFIGURACIÓN GENERAL
; ================================================================

[Setup]

AppId={{9D720930-63BC-46AD-A611-5B268301EA19}

AppName={#NombreAplicacion}
AppVersion={#VersionAplicacion}
AppVerName={#NombreAplicacion} {#VersionAplicacion}

DefaultDirName={autopf}\Convertidor de Archivos
DefaultGroupName=Convertidor de Archivos

UninstallDisplayName={#NombreAplicacion}
UninstallDisplayIcon={app}\{#EjecutableAplicacion}

OutputDir=instalador
OutputBaseFilename={#NombreInstalador}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

PrivilegesRequired=admin

Compression=lzma2/max
SolidCompression=yes

WizardStyle=modern

DisableWelcomePage=no
DisableProgramGroupPage=yes

AlwaysShowComponentsList=yes
FlatComponentsList=no
ShowComponentSizes=yes

CloseApplications=yes
RestartApplications=no

CreateAppDir=yes
CreateUninstallRegKey=yes

VersionInfoVersion=1.1.0.0
VersionInfoProductName={#NombreAplicacion}
VersionInfoProductVersion={#VersionAplicacion}
VersionInfoDescription=Instalador de {#NombreAplicacion}


; ================================================================
; ICONO DEL INSTALADOR
; ================================================================

#if FileExists("recursos\iconos\FileConverter.ico")

SetupIconFile=recursos\iconos\FileConverter.ico

#endif


; ================================================================
; TIPOS DE INSTALACIÓN
; ================================================================

[Types]

Name: "completa"; Description: "Instalación completa"


; ================================================================
; COMPONENTES
; ================================================================

[Components]

Name: "principal"; \
    Description: "Aplicación principal"; \
    Types: completa; \
    Flags: fixed

Name: "principal\documentos"; \
    Description: "Compatibilidad con documentos"; \
    Types: completa; \
    Flags: fixed

Name: "principal\documentos\libreoffice"; \
    Description: "LibreOffice"; \
    Types: completa; \
    Flags: fixed

Name: "principal\imagenes"; \
    Description: "Compatibilidad avanzada con imágenes"; \
    Types: completa; \
    Flags: fixed

Name: "principal\imagenes\imagemagick"; \
    Description: "ImageMagick"; \
    Types: completa; \
    Flags: fixed

Name: "principal\comprimidos"; \
    Description: "Archivos comprimidos"; \
    Types: completa; \
    Flags: fixed

Name: "principal\comprimidos\7zip"; \
    Description: "7-Zip"; \
    Types: completa; \
    Flags: fixed

Name: "principal\libros"; \
    Description: "Documentos, libros y marcado"; \
    Types: completa; \
    Flags: fixed

Name: "principal\libros\pandoc"; \
    Description: "Pandoc"; \
    Types: completa; \
    Flags: fixed


; ================================================================
; ARCHIVOS PRINCIPALES
; ================================================================

[Files]


; ----------------------------------- ;
;        Ejecutable principal          ;
; ----------------------------------- ;

Source: "{#CarpetaCompilada}\{#EjecutableAplicacion}"; \
    DestDir: "{app}"; \
    Flags: ignoreversion; \
    Components: principal


; ----------------------------------- ;
;     Dependencias internas Python     ;
; ----------------------------------- ;

Source: "{#CarpetaCompilada}\_internal\*"; \
    DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal


; ================================================================
; LIBREOFFICE
; ================================================================

Source: "{#CarpetaCompilada}\motores\libreoffice\*"; \
    DestDir: "{app}\motores\libreoffice"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\documentos\libreoffice


; ================================================================
; IMAGEMAGICK
; ================================================================

Source: "{#CarpetaCompilada}\motores\imagemagick\*"; \
    DestDir: "{app}\motores\imagemagick"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\imagenes\imagemagick


; ================================================================
; 7-ZIP
; ================================================================

Source: "{#CarpetaCompilada}\motores\7zip\*"; \
    DestDir: "{app}\motores\7zip"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\comprimidos\7zip


; ================================================================
; PANDOC
; ================================================================

Source: "{#CarpetaCompilada}\motores\pandoc\*"; \
    DestDir: "{app}\motores\pandoc"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\libros\pandoc


; ================================================================
; LICENCIAS Y DOCUMENTACIÓN
; ================================================================

Source: "{#CarpetaCompilada}\licencias_terceros\*"; \
    DestDir: "{app}\licencias_terceros"; \
    Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; \
    Components: principal

Source: "{#CarpetaCompilada}\README.txt"; \
    DestDir: "{app}"; \
    Flags: ignoreversion skipifsourcedoesntexist; \
    Components: principal

Source: "{#CarpetaCompilada}\LICENSE.txt"; \
    DestDir: "{app}"; \
    Flags: ignoreversion skipifsourcedoesntexist; \
    Components: principal


; ================================================================
; TAREAS OPCIONALES
; ================================================================

[Tasks]

Name: "desktopicon"; \
    Description: "Crear un acceso directo en el escritorio"; \
    GroupDescription: "Accesos directos:"; \
    Flags: unchecked


; ================================================================
; ACCESOS DIRECTOS
; ================================================================

[Icons]

Name: "{group}\Convertidor de Archivos"; \
    Filename: "{app}\{#EjecutableAplicacion}"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\Convertidor de Archivos"; \
    Filename: "{app}\{#EjecutableAplicacion}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon


; ================================================================
; EJECUTAR AL FINALIZAR
; ================================================================

[Run]

Filename: "{app}\{#EjecutableAplicacion}"; \
    Description: "Ejecutar Convertidor de Archivos"; \
    WorkingDir: "{app}"; \
    Flags: nowait postinstall skipifsilent