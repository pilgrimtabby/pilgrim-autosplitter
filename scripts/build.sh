#!/usr/bin/env bash

# IMPORTANT: After building, you MUST zip the app yourself, or it will not run when unzipped after
#            being downloaded from GitHub. I have no idea why, but it works.

# To build on MacOS, navigate to the project root directory and run this (`bash scripts/build.sh`)
# A working app will be placed in /dist

# Requirements: PyInstaller (`pip install -U pyinstaller`)
#               Platypus (command line tool required, see https://github.com/sveinbjornt/Platypus)

# I use Platypus because of an issue (apparently, a well-documented one) that makes building a
# single-file Python application with PyInstaller on MacOS impossible. Injecting the app into
# Platypus allows it to open and retain an icon, but we still have to deal with the terminal
# window popping up. Oh, well...

# Also, I tried, but I couldn't find a way to make the correct icon show up on the task bar.


# Build the executible
pyinstaller src/pilgrim_autosplitter.py --noconfirm --onefile --windowed --name "Pilgrim Autosplitter"

# Inject the app into a Platypus app
/usr/local/bin/platypus --background --quit-after-execution --app-icon 'resources/icon-macos.icns'  --name 'Pilgrim Autosplitter'  --interface-type 'None'  --interpreter '/bin/bash'  --author 'pilgrim_tabby'   --bundle-identifier org.pilgrimtabby.PilgrimAutosplitter --bundled-file 'dist/Pilgrim Autosplitter'  'scripts/bootstrap.sh'

# Remove the build artifacts we don't use
rm -r build
rm -r dist
rm "Pilgrim Autosplitter.spec"

# Move the built app into /dist
mkdir dist
mv "scripts/Pilgrim Autosplitter.app" "dist/Pilgrim Autosplitter.app"
