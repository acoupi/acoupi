#!bin/bash

sudo ln -sf $HOME/acoupi/src/acoupi/services/run_batdetect2.service /usr/lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable run_batdetect2.service
sudo systemctl start run_batdetect2.service
systemctl status run_batdetect2.service
