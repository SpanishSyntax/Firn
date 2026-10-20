{
  description = "Firn - Instant GitHub-Flavored Markdown (GFM) Native Desktop Viewer";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }: let
    systems = flake-utils.lib.defaultSystems;
  in
    flake-utils.lib.eachSystem systems (system: let
      pkgs = import nixpkgs {inherit system;};
      firnPackage = pkgs.callPackage ./default.nix {};
    in {
      packages = {
        default = firnPackage;
        firn = firnPackage;
      };

      apps = {
        default = {
          type = "app";
          program = "${firnPackage}/bin/firn";
        };
        firn = {
          type = "app";
          program = "${firnPackage}/bin/firn";
        };
      };

      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.setuptools
          python3Packages.pytest
          python3Packages.grip
          python3Packages.pywebview
          python3Packages.pygobject3
          gobject-introspection
          gtk3
          webkitgtk_4_1
          glib-networking
          gsettings-desktop-schemas
        ];

        shellHook = ''
          export GI_TYPELIB_PATH="${pkgs.lib.makeSearchPath "lib/girepository-1.0" [
            pkgs.gtk3
            pkgs.webkitgtk_4_1
            pkgs.gobject-introspection
            pkgs.pango
            pkgs.gdk-pixbuf
            pkgs.atk
            pkgs.harfbuzz
          ]}''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
          export GIO_EXTRA_MODULES="${pkgs.glib-networking}/lib/gio/modules''${GIO_EXTRA_MODULES:+:$GIO_EXTRA_MODULES}"
          export PYWEBVIEW_GUI="gtk"
        '';
      };
    })
    // {
      overlays = {
        default = final: prev: {
          firn = final.callPackage ./default.nix {};
        };
        firn = self.overlays.default;
      };

      nixosModules = {
        default = self.nixosModules.firn;
        firn = {
          config,
          lib,
          pkgs,
          ...
        }: let
          cfg = config.programs.firn;
          system = pkgs.stdenv.hostPlatform.system;
          defaultFirn = self.packages.${system}.default;
        in {
          options.programs.firn = {
            enable = lib.mkEnableOption "Firn - Instant GitHub-Flavored Markdown (GFM) native desktop viewer";

            package = lib.mkOption {
              type = lib.types.package;
              default = defaultFirn;
              description = "The Firn package to use.";
            };
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [cfg.package];
          };
        };
      };

      homeManagerModules = {
        default = self.homeManagerModules.firn;
        firn = {
          config,
          lib,
          pkgs,
          ...
        }: let
          cfg = config.programs.firn;
          tomlFormat = pkgs.formats.toml {};
          system = pkgs.stdenv.hostPlatform.system;
          defaultFirn = self.packages.${system}.default;
        in {
          options.programs.firn = {
            enable = lib.mkEnableOption "Firn - Instant GitHub-Flavored Markdown (GFM) native desktop viewer";

            package = lib.mkOption {
              type = lib.types.package;
              default = defaultFirn;
              description = "The Firn package to use.";
            };

            settings = lib.mkOption {
              type = tomlFormat.type;
              default = {};
              description = "Configuration written to ~/.config/firn/firn.toml.";
            };
          };

          config = lib.mkIf cfg.enable {
            home.packages = [cfg.package];

            xdg.configFile."firn/firn.toml" = lib.mkIf (cfg.settings != {}) {
              source = tomlFormat.generate "firn.toml" cfg.settings;
            };
          };
        };
      };
    };
}
