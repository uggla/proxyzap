# proxyzap
A simple script to change Gnome3 proxy settings based on connected subnet

[Screenshot1](screenshots/1.png)


# Installation

* Clone the repository
```
git clone https://github.com/uggla/proxyzap.git
```

* Run the install.sh script. This script will create a systemd service file and link it with your systemd user settings.


# Service management

* Status
```
systemctl --user status proxyzap.service
```

* Start
```
systemctl --user start proxyzap.service
```

* Stop
```
systemctl --user stop proxyzap.service
```



# Configuration file

```
[proxyzap]
SUBGW = "192.168.0.254"
PROXY = "myproxy.mydomain.local"
PROXYPORT = "8080"
PROXYIGNORE = localhost, 127.0.0.0/8, ::1
DEBUG = True
```

* SUBGW: Is the gateway off the network that requires proxy settings.
* PROXY: Proxy host name.
* PROXYPORT: Proxy port used.
* PROXYIGNORE: Hosts or subnets that do not need a proxy to connect to.
* DEBUG = True|False, set the log verbosity.


# Limitations
Currently it can manage only one proxy.
