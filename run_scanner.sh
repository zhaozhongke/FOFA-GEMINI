#!/bin/bash

# This script is a simple wrapper to run the FOFA Gemini key scanner.
# It's intended to be called by a scheduler like cron.

# Get the directory where the script is located to ensure correct pathing
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script's directory. This is important for cron jobs so that
# the python script can find its config file and the database file.
cd "$DIR"

echo "Starting FOFA scanner run at $(date)"
python3 main.py
echo "Scanner run finished at $(date)"
