#!/usr/bin/env bash

echo 'mass apk installer v3.0'

# restore from zip file
./apk_mass_install -i archive.zip

# restore from folder
./apk_mass_install -i folder/path

# restore from encrypted zip file
./apk_mass_install -i encrypted.zip
