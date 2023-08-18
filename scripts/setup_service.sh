sudo ln -sf $HOME/acoupi/src/acoupi/services/acoupi_testing.service /usr/lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable acoupi_testing.service
sudo systemctl start acoupi_testing.service
systemctl status acoupi_testing.service
