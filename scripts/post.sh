#!/bin/bash
# post.sh — GNOME tweaks for workspace switcher & shortcuts

# Make sure D-Bus is available
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    echo "Error: No D-Bus session detected. Please run this script from within your GNOME session."
    exit 1
fi

echo "Disabling top-left hot corner (workspace switcher)..."
gsettings set org.gnome.desktop.interface enable-hot-corners false

echo "Disabling all GNOME Shell keybindings..."
# This will unbind most shell shortcuts
SCHEMA="org.gnome.shell.keybindings"
for key in $(gsettings list-keys $SCHEMA); do
    gsettings set $SCHEMA "$key" "[]"
done

echo "Disabling Nautilus (file manager) shortcuts..."
SCHEMA="org.gnome.desktop.wm.keybindings"
for key in $(gsettings list-keys $SCHEMA); do
    gsettings set $SCHEMA "$key" "[]"
done

echo "Disabling media keybindings..."
SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
for key in $(gsettings list-keys $SCHEMA); do
    gsettings set $SCHEMA "$key" "[]"
done

echo "Done. You may need to log out and log back in for all changes to take effect."
