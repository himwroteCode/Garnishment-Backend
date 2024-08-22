#!/bin/bash

# Update the package list
apt-get update

# Install necessary packages for ODBC driver installation
apt-get install -y curl apt-transport-https

# Import the Microsoft GPG keys
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add the Microsoft SQL Server Ubuntu repository
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update the package list after adding the new repository
apt-get update

# Install the ODBC driver for SQL Server
ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
