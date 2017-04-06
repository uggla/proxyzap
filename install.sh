#/bin/bash


#######################################################################
#                    proxyzap installation script                     #
#######################################################################

# Use strict mode
set -euo pipefail
IFS=$'\n\t'

CURRENTDIR=$(dirname $0)
cd $CURRENTDIR
CURRENTDIR=$(pwd)

# Write a systemd file
cat >proxyzap.service << EOF
[Unit]
Description=proxyzap - Change Gnome proxy based on connected subnet

[Service]
WorkingDirectory=$CURRENTDIR
ExecStart=$CURRENTDIR/proxyzap.py
Restart=on-failure
KillSignal=SIGTERM

[Install]
WantedBy=default.target
EOF

# Add it to systemd user configuration
if [[ ! -L ~/.config/systemd/user/proxyzap.service ]]; then
	ln -s $CURRENTDIR/proxyzap.service ~/.config/systemd/user/proxyzap.service
fi

# Start service
systemctl --user start proxyzap.service

