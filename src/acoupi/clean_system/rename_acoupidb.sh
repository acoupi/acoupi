#!bin/bash

# Get the current month and year"
#month=$(date +%B | tr '[:upper:]' '[:lower:]')
time=$(date +%H%M%S)
month=$(date +%m)
year=$(date +%y)
renamed_file="acoupi_${month}${year}_${time}.db"

# Move the acoupi.db
cd ~/acoupi/src/acoupi/components/message_stores/sqlite
mv acoupi.db "$renamed_file"
cd ~/acoupi/src/acoupi/components/stores/sqlite
mv acoupi.db "$renamed_file"