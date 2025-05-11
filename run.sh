#!/bin/bash

# Set your working directory
PROJECT_DIR="/home/jee/Desktop/bot"     # full path to your project
VENV_DIR="venv"                         # venv folder inside project dir
SCRIPT_DIR="v6"                         # subfolder inside project dir
SCRIPT_NAME="main.py"                   # run Python script
SCRIPT2_NAME="website.py"				# open the website

# Open a new terminal and show Python output, keeping terminal open after
lxterminal --working-directory="$PROJECT_DIR" --command="bash -c '
source $VENV_DIR/bin/activate && 
cd $SCRIPT_DIR && 
python3 $SCRIPT_NAME; 
echo \"\n\n[?] Script finished. Press Enter to exit...\"; 
read; exec bash'" &

lxterminal --working-directory="$PROJECT_DIR" --command="bash -c '
source $VENV_DIR/bin/activate && 
cd $SCRIPT_DIR && 
python3 $SCRIPT2_NAME; 
read; exec bash'"
