#!/bin/bash
XML_DIR="uploads"
SCRIPT_DIR="script_files"
if [ ! -e $XML_DIR ]; then
        mkdir uploads
fi
if [ ! -e $SCRIPT_DIR ]; then
        mkdir script_files
fi
#nohup python3 -u ./application.py 
#nodemon --exec python3 ./application.py
nodemon --ignore upload/ --exec python3 ./application.py
