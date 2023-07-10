#!bin/bash

sudo ln -sf $HOME/acoupi/src/acoupi/services/run_acoupi.service /usr/lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable run_acoupi.service
sudo systemctl start run_acoupi.service
systemctl status run_acoupi.service
