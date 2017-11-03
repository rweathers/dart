#!/bin/sh -e

rm -f dart.deb

ln -sf ../lib/dart.py debian/usr/bin/dart

cp ../../source/dart.py           debian/usr/lib/dart.py
cp ../../source/dart/*.py         debian/usr/lib/dart/
cp ../../source/dart.template.ini debian/etc/dart.conf

cp ../resources/dart.png debian/usr/share/doc/dart/dart.png

mv debian/usr/share/applications/desktop.txt debian/usr/share/applications/dart.desktop

gzip -9 debian/usr/share/doc/dart/changelog

perl -p -i -e 's/{path}dart.ini/\/etc\/dart.conf/g' debian/usr/lib/dart.py
perl -p -i -e 's/{path}dart.err/\/tmp\/dart.err/g' debian/usr/lib/dart.py

sudo chown -R root:root debian

dpkg --build debian

sudo chown -R rweathers:rweathers debian

mv debian.deb dart.deb

gunzip debian/usr/share/doc/dart/changelog.gz
mv debian/usr/share/applications/dart.desktop debian/usr/share/applications/desktop.txt
rm debian/usr/share/doc/dart/dart.png
rm debian/etc/dart.conf
rm debian/usr/lib/dart/*
rm debian/usr/lib/dart.py

rm debian/usr/bin/dart

lintian dart.deb
