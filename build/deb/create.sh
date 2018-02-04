#!/bin/sh -e

rm -f dart.deb

mkdir debian/etc
mkdir debian/usr/bin
mkdir debian/usr/lib
mkdir debian/usr/lib/dart
mkdir debian/usr/lib/dart/classes

ln -sf ../lib/dart/dart.py debian/usr/bin/dart

cp ../../source/dart.py           debian/usr/lib/dart/dart.py
cp ../../source/classes/*.py      debian/usr/lib/dart/classes
cp ../../source/dart.template.ini debian/etc/dart.conf

cp ../resources/dart.png debian/usr/share/doc/dart/dart.png

mv debian/usr/share/applications/desktop.txt debian/usr/share/applications/dart.desktop

gzip -9 debian/usr/share/doc/dart/changelog

perl -p -i -e 's/{path}dart.ini/\/etc\/dart.conf/g' debian/usr/lib/dart/dart.py
perl -p -i -e 's/{path}dart.err/\/tmp\/dart.err/g ' debian/usr/lib/dart/dart.py

sudo chown -R root:root debian

dpkg --build debian

sudo chown -R rweathers:rweathers debian

mv debian.deb dart.deb

gunzip debian/usr/share/doc/dart/changelog.gz
mv debian/usr/share/applications/dart.desktop debian/usr/share/applications/desktop.txt
rm debian/usr/share/doc/dart/dart.png
rm debian/etc/dart.conf
rm debian/usr/lib/dart/classes/*
rm debian/usr/lib/dart/dart.py

rm debian/usr/bin/dart

rmdir debian/usr/lib/dart/classes
rmdir debian/usr/lib/dart
rmdir debian/usr/lib
rmdir debian/usr/bin
rmdir debian/etc

lintian dart.deb
