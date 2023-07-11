#!bin/bash

# Get the current month and year"
#month=$(date +%B | tr '[:upper:]' '[:lower:]')
month=$(date +%m)
year=$(date +%y)
echo $month
echo $year
renamed_file="acoupi_${month}${year}.db"
echo $renamed_file

# Move the acoupi.db
cd ~/acoupi/src/acoupi/components/message_stores/sqlite
mv acoupi.db "$renamed_file"
cd ~/acoupi/src/acoupi/components/stores/sqlite
mv acoupi.db "$renamed_file"