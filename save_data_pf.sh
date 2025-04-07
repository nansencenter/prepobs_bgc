#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <year>"
  exit 1
fi

year=$1

cd config
sed "s/YYYY/$year/g" default/save_data_pf.toml > save_data.toml

cd ..
make run-save-data

