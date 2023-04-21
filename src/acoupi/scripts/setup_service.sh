sudo ln -sf services/acoupi_testing.service /usr/lib/systemd/system
sudo systemctl enable acoupi_testing.service
sudo systemctl start acoupi_testing.service

systemctl is-active --quiet acoupi_testing.service && echo acoupi service is running || echo acoupi services is not running
