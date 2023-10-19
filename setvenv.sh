#!/bin/bash

# Add python venv and activate
python3 -m venv ./venv
source ./venv/bin/activate

# Install required packages
pip3 install -r requirements.txt