#!/bin/sh -e

version="0.4.0-beta"

cd ../release

mkdir $version
cd $version

mkdir script

cp ../../source/dart.py           script/dart.py
cp ../../source/dart.template.ini script/dart.conf

cp ../../COPYING script/COPYING

perl -p -i -e 's/dart.ini/dart.conf/g' script/dart.py

cd script
zip -rq ../dart_${version}_script.zip *
cd ..

rm -r script/*
rmdir script

mkdir executable

cp ../../build/exe/dart-gui.exe executable/dart-gui.exe
cp ../../build/exe/dart.exe     executable/dart.exe

cp ../../source/dart.template.ini executable/dart.ini

cp ../../COPYING executable/COPYING

cd executable
zip -q ../dart_${version}_executable.zip *
cd ..

rm -r executable/*
rmdir executable

cp ../../build/deb/dart.deb dart_${version}_debian.deb
cp ../../build/msi/dart.msi dart_${version}_windows.msi
