#!/usr/bin/env bash

# To build on MacOS, navigate to the project root directory and run this (`bash scripts/build.sh`)
pyinstaller src/pilgrim_autosplitter.py --noconfirm --onefile --windowed --name "Pilgrim Autosplitter"
/usr/local/bin/platypus --background --quit-after-execution --app-icon 'resources/icon-macos.icns'  --name 'Pilgrim Autosplitter'  --interface-type 'None'  --interpreter '/bin/bash'  --author 'pilgrim_tabby'   --bundle-identifier org.pilgrimtabby.PilgrimAutosplitter --bundled-file 'dist/Pilgrim Autosplitter'  'scripts/bootstrap.sh'

rm -r build
rm -r dist
rm "Pilgrim Autosplitter.spec"

mkdir dist
mv "scripts/Pilgrim Autosplitter.app" "dist/Pilgrim Autosplitter.app"
