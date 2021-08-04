{ pkgs ? import <nixpkgs> {} }:

let
  python-with-packages = pkgs.python39.withPackages (pyPkgs: with pyPkgs; [
    httpx
    python-rapidjson
    build
  ]);
in
  pkgs.mkShell {
    name = "py-vitals";
    buildInputs = [
      python-with-packages
    ];
  }