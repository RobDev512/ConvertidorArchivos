; ================================================================
; CONVERTIDOR DE ARCHIVOS 1.1.1
; INSTALADOR OFICIAL
; ================================================================


#define NombreAplicacion "Convertidor de Archivos"
#define VersionAplicacion "1.1.1"
#define EjecutableAplicacion "ConvertidorArchivos.exe"
#define CarpetaCompilada "dist\ConvertidorArchivos"
#define NombreInstalador "ConvertidorArchivos_Setup_1.1.1"


; ================================================================
; CONFIGURACION GENERAL
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
DisableReadyPage=no

AlwaysShowComponentsList=yes
FlatComponentsList=no
ShowComponentSizes=yes

CloseApplications=yes
RestartApplications=no

CreateAppDir=yes
CreateUninstallRegKey=yes

UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousTasks=yes

VersionInfoVersion=1.1.1.0
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
; TIPOS DE INSTALACION
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
    Description: "Herramientas y compatibilidad avanzada con imágenes"; \
    Types: completa; \
    Flags: fixed

Name: "principal\imagenes\imagemagick"; \
    Description: "ImageMagick"; \
    Types: completa; \
    Flags: fixed

Name: "principal\imagenes\realesrgan"; \
    Description: "Real-ESRGAN · Mejora de calidad con IA"; \
    Types: completa; \
    Flags: fixed

Name: "principal\imagenes\quitarfondo"; \
    Description: "Modelos IA · Quitar fondo"; \
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

Source: "{#CarpetaCompilada}\{#EjecutableAplicacion}"; \
    DestDir: "{app}"; \
    Flags: ignoreversion; \
    Components: principal

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
; REAL-ESRGAN
; ================================================================

Source: "{#CarpetaCompilada}\motores\realesrgan\*"; \
    DestDir: "{app}\motores\realesrgan"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\imagenes\realesrgan


; ================================================================
; QUITAR FONDO
; ================================================================

Source: "{#CarpetaCompilada}\motores\quitar_fondo\*"; \
    DestDir: "{app}\motores\quitar_fondo"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Components: principal\imagenes\quitarfondo


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
; LICENCIAS Y DOCUMENTACION
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
; LIMPIEZA AL ACTUALIZAR
; ================================================================

[InstallDelete]

Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\motores"
Type: filesandordirs; Name: "{app}\licencias_terceros"


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


; ================================================================
; INFORMACION DE TAMANO Y ACTUALIZACION
; ================================================================

[Code]

var
  PaginaTamano: TWizardPage;
  EtiquetaTipo: TNewStaticText;
  EtiquetaPaquete: TNewStaticText;
  EtiquetaInstalacion: TNewStaticText;
  EtiquetaNota: TNewStaticText;


// ================================================================
// FORMATEAR BYTES
// ================================================================

function FormatearBytes(
  Tamano: Int64
): String;
begin

  if Tamano >= 1073741824 then
  begin

    Result :=
      IntToStr(
        (Tamano + 536870912) div 1073741824
      )
      + ' GB';

  end
  else if Tamano >= 1048576 then
  begin

    Result :=
      IntToStr(
        (Tamano + 524288) div 1048576
      )
      + ' MB';

  end
  else if Tamano >= 1024 then
  begin

    Result :=
      IntToStr(
        (Tamano + 512) div 1024
      )
      + ' KB';

  end
  else
  begin

    Result :=
      IntToStr(
        Tamano
      )
      + ' bytes';

  end;

end;


// ================================================================
// OBTENER VERSION INSTALADA
// ================================================================

function ObtenerVersionInstalada(): String;
var
  ClaveDesinstalacion: String;
begin

  ClaveDesinstalacion :=
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\' +
    '{9D720930-63BC-46AD-A611-5B268301EA19}_is1';

  Result := '';


  // ----------------------------------- //
  //         Registro de 64 bits         //
  // ----------------------------------- //

  if RegQueryStringValue(
    HKLM64,
    ClaveDesinstalacion,
    'DisplayVersion',
    Result
  ) then
  begin

    Exit;

  end;


  // ----------------------------------- //
  //         Registro de 32 bits         //
  // ----------------------------------- //

  if RegQueryStringValue(
    HKLM32,
    ClaveDesinstalacion,
    'DisplayVersion',
    Result
  ) then
  begin

    Exit;

  end;


  // ----------------------------------- //
  //         Registro de usuario         //
  // ----------------------------------- //

  if RegQueryStringValue(
    HKCU,
    ClaveDesinstalacion,
    'DisplayVersion',
    Result
  ) then
  begin

    Exit;

  end;

end;


// ================================================================
// ACTUALIZAR PAGINA DE TAMANO
// ================================================================

procedure ActualizarPaginaTamano();
var
  TamanoInstalador: Int64;
  VersionAnterior: String;
begin

  VersionAnterior :=
    ObtenerVersionInstalada();


  // ----------------------------------- //
  //      Instalacion o actualizacion    //
  // ----------------------------------- //

  if VersionAnterior <> '' then
  begin

    EtiquetaTipo.Caption :=
      'Actualización detectada: '
      + VersionAnterior
      + ' → {#VersionAplicacion}';

  end
  else
  begin

    EtiquetaTipo.Caption :=
      'Instalación nueva de la versión '
      + '{#VersionAplicacion}';

  end;


  // ----------------------------------- //
  //        Tamano del instalador        //
  // ----------------------------------- //

  if FileSize64(
    ExpandConstant(
      '{srcexe}'
    ),
    TamanoInstalador
  ) then
  begin

    EtiquetaPaquete.Caption :=
      'Tamaño del paquete: '
      + FormatearBytes(
          TamanoInstalador
        );

  end
  else
  begin

    EtiquetaPaquete.Caption :=
      'Tamaño del paquete: no disponible';

  end;


  // ----------------------------------- //
  //        Espacio de instalacion       //
  // ----------------------------------- //

  EtiquetaInstalacion.Caption :=
    WizardForm.ComponentsDiskSpaceLabel.Caption;

end;


// ================================================================
// CREAR PAGINA DE TAMANO
// ================================================================

procedure InitializeWizard();
begin

  PaginaTamano :=
    CreateCustomPage(
      wpSelectComponents,
      'Tamaño de la instalación',
      'Revisa el tamaño antes de continuar.'
    );


  // ----------------------------------- //
  //        Tipo de instalacion          //
  // ----------------------------------- //

  EtiquetaTipo :=
    TNewStaticText.Create(
      PaginaTamano
    );

  EtiquetaTipo.Parent :=
    PaginaTamano.Surface;

  EtiquetaTipo.Left :=
    0;

  EtiquetaTipo.Top :=
    16;

  EtiquetaTipo.Width :=
    PaginaTamano.SurfaceWidth;

  EtiquetaTipo.AutoSize :=
    False;

  EtiquetaTipo.WordWrap :=
    True;

  EtiquetaTipo.Height :=
    36;


  // ----------------------------------- //
  //        Tamano del paquete           //
  // ----------------------------------- //

  EtiquetaPaquete :=
    TNewStaticText.Create(
      PaginaTamano
    );

  EtiquetaPaquete.Parent :=
    PaginaTamano.Surface;

  EtiquetaPaquete.Left :=
    0;

  EtiquetaPaquete.Top :=
    68;

  EtiquetaPaquete.Width :=
    PaginaTamano.SurfaceWidth;

  EtiquetaPaquete.AutoSize :=
    False;

  EtiquetaPaquete.Height :=
    24;


  // ----------------------------------- //
  //        Espacio requerido            //
  // ----------------------------------- //

  EtiquetaInstalacion :=
    TNewStaticText.Create(
      PaginaTamano
    );

  EtiquetaInstalacion.Parent :=
    PaginaTamano.Surface;

  EtiquetaInstalacion.Left :=
    0;

  EtiquetaInstalacion.Top :=
    104;

  EtiquetaInstalacion.Width :=
    PaginaTamano.SurfaceWidth;

  EtiquetaInstalacion.AutoSize :=
    False;

  EtiquetaInstalacion.WordWrap :=
    True;

  EtiquetaInstalacion.Height :=
    40;


  // ----------------------------------- //
  //              Nota                   //
  // ----------------------------------- //

  EtiquetaNota :=
    TNewStaticText.Create(
      PaginaTamano
    );

  EtiquetaNota.Parent :=
    PaginaTamano.Surface;

  EtiquetaNota.Left :=
    0;

  EtiquetaNota.Top :=
    162;

  EtiquetaNota.Width :=
    PaginaTamano.SurfaceWidth;

  EtiquetaNota.AutoSize :=
    False;

  EtiquetaNota.WordWrap :=
    True;

  EtiquetaNota.Height :=
    72;

  EtiquetaNota.Caption :=
    'El paquete incluye los motores y modelos de IA necesarios '
    + 'para que las herramientas funcionen de forma local. '
    + 'En una actualización se utiliza el instalador completo, '
    + 'aunque los archivos anteriores se reemplazan automáticamente.';

end;


// ================================================================
// CAMBIAR PAGINA
// ================================================================

procedure CurPageChanged(
  CurPageID: Integer
);
begin

  if CurPageID = PaginaTamano.ID then
  begin

    ActualizarPaginaTamano();

  end;

end;