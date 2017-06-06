#/bin/bash


#######################################################################
#                    proxyzap installation script                     #
#######################################################################

# Use strict mode
set -euo pipefail
IFS=$'\n\t'

DNF_CONF_FILE="/etc/dnf/dnf.conf"

declare -i ENABLE_DNF_PROXY=0


function usage(){
    echo "usage: $0 [OPTIONS]"
    echo "  -h|--help"
    echo "              display this message and exit"
    echo "  -d|--dnfproxy"
    echo "              enable dnf proxy configuration"
    echo "              note: require the user to have write access"
    echo "                    to the /etc/dnf/dnf.conf file"
}

function enable_dnf_proxy(){

    echo "Configuring control of dnf proxy (file: $DNF_CONF_FILE)"

    #user's group owns the file
    chown root:$USER $DNF_CONF_FILE

    #enable write access for user's group
    chmod g+w $DNF_CONF_FILE
 
    echo "Configuration done"
}


ARGS=$(getopt -o hd --long "help,dnfproxy" -- "$@")


eval set -- "$ARGS"

while true; do
    case $1 in
        -h|--help)
            usage; exit 1 ;;
        -d|--dnfproxy)
            ENABLE_DNF_PROXY=1 ; shift ;;
        --) shift; break ;;
        *) usage; exit 1;;
    esac
done


if [[  $ENABLE_DNF_PROXY -eq 1 ]]; then
    
    #check if we are root
    if [[ $EUID -ne 0 ]]; then
        echo "WARNING: You are not running this script as root !"
        echo "In order to enable the dnf proxy configuration,   "
        echo "you must have root privileges                     "
        exit 1
    fi

    enable_dnf_proxy
fi



CURRENTDIR=$(dirname $0)
cd $CURRENTDIR
CURRENTDIR=$(pwd)


#In case the script is run with sudo, make sure the systemd files are place within
# the calling user's home

USERHOME=$(eval echo ~$USER)



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

# Create systemd local user config dir
if [[ ! -d $USERHOME/.config/systemd ]]; then
    mkdir -p $USERHOME/.config/systemd/user
fi




# Add it to systemd user configuration
if [[ ! -f $USERHOME/.config/systemd/user/proxyzap.service ]]; then
     # Use a physical link because symbolic link causes some
     # systemd issues
 	ln $CURRENTDIR/proxyzap.service $USERHOME/.config/systemd/user/proxyzap.service
 fi


# Start service
su - $USER -c "systemctl --user enable proxyzap.service"
su - $USER -c "systemctl --user start proxyzap.service"

