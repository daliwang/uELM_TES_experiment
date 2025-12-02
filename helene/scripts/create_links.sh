#!/bin/bash
cd "$(dirname "$0")"
python3 forcing_domain_link_creation.py
echo 'Soft links created under ../atm_forcing.datm7.km.1d' 
