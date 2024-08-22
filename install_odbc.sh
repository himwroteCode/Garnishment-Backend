#!/bin/bash

# Install dependencies
sudo apt-get update
sudo apt-get install -y curl apt-transport-https gnupg

# Add Microsoft package signing key and repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list

# Update package list and install ODBC Driver 18 for SQL Server
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
sudo apt-get install -y unixodbc-dev

# Install additional ODBC drivers if necessary
sudo apt-get install -y odbcinst unixodbc

echo "ODBC Driver 18 for SQL Server installed successfully."
