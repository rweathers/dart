#! /usr/bin/python3

import base64

s = ""
with open("dart.png", "rb") as f: s = base64.b64encode(f.read())
with open("base64.txt", "wb") as f: f.write(s);
