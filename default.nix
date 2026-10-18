{
  pkgs ? import <nixpkgs> {},
  lib ? pkgs.lib,
  python3Packages ? pkgs.python3Packages,
}: let
  gripPkg = python3Packages.grip;
in
  python3Packages.buildPythonApplication {
    pname = "firn";
    version = "0.1.0";
    src = ./.;
    pyproject = true;

    build-system = [
      python3Packages.setuptools
    ];

    nativeBuildInputs = [
      pkgs.makeWrapper
      pkgs.wrapGAppsHook3
      pkgs.gobject-introspection
    ];

    buildInputs = [
      pkgs.glib
      pkgs.gtk3
      pkgs.webkitgtk_4_1
      pkgs.glib-networking
      pkgs.gsettings-desktop-schemas
    ];

    dependencies = [
      gripPkg
      python3Packages.pywebview
      python3Packages.pygobject3
    ];

    dontWrapGApps = true;

    preFixup = ''
      makeWrapperArgs+=(
        "''${gappsWrapperArgs[@]}"
        --prefix PATH : "${lib.makeBinPath [gripPkg]}"
        --set-default PYWEBVIEW_GUI "gtk"
      )
    '';

    doCheck = false;

    meta = with lib; {
      description = "Instant GitHub-Flavored Markdown (GFM) native desktop document viewer";
      homepage = "https://github.com/SpanishSyntax/Firn";
      license = licenses.mit;
      mainProgram = "firn";
      platforms = platforms.linux ++ platforms.darwin;
    };
  }
