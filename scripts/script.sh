#!/bin/bash

set -e

USERNAME="lockeddown"
SHARED_FOLDER="/shared"
REPO_URL="https://github.com/Hung-nd233960/MachineLearningET4248E"
GROUPNAME="sharedgroup"
DESKTOP_DIR="/home/$NEW_USER/Desktop"
# 1. Create shared group
if ! getent group "$GROUPNAME" >/dev/null; then
    echo "[INFO] Creating group: $GROUPNAME"
    groupadd "$GROUPNAME"
fi

# 2. Create user & add to group
if ! id "$USERNAME" >/dev/null 2>&1; then
    echo "[INFO] Creating user: $USERNAME"
    useradd -m -G "$GROUPNAME" "$USERNAME"
    echo "[INFO] Set password for $USERNAME:"
    passwd "$USERNAME"
else
    echo "[INFO] User exists. Adding to group $GROUPNAME"
    usermod -aG "$GROUPNAME" "$USERNAME"
fi

# 3. Create shared folder
mkdir -p "$SHARED_FOLDER"
chown :"$GROUPNAME" "$SHARED_FOLDER"
chmod 2775 "$SHARED_FOLDER"

# 4. Install dependencies for development
echo "[INFO] Installing Python, Git, pipx, Poetry..."
apt update
apt install -y python3 python3-pip python3-venv git pipx npm nodejs

# Ensure pipx path is in global shell init
sudo -u "$USERNAME" pipx ensurepath

# Install poetry via pipx (user-level install)
sudo -u "$USERNAME" pipx install poetry

# 5. Clone repo into user's home
REPO_NAME=$(basename "$REPO_URL" .git)
sudo -u "$USERNAME" git clone "$REPO_URL" "/home/$USERNAME/$REPO_NAME"

# 6. Switch to development branch
cd "/home/$USERNAME/$REPO_NAME"
sudo -u "$USERNAME" git fetch origin
sudo -u "$USERNAME" git checkout development

# 7. Install Poetry dependencies
sudo -u "$USERNAME" pipx run poetry install
cd "/home/$USERNAME/$REPO_NAME/electron-app" 
sudo -u "$USERNAME" npm install 

# 9. Install GNOME Shell extensions
echo "[INFO] Installing GNOME Shell extensions..."
apt install -y gnome-shell-extensions
apt install -y netcat-traditional
# Create Desktop directory if not present
mkdir -p "$DESKTOP_DIR"

# Create post.sh
cat << 'EOF' > "$DESKTOP_DIR/post.sh"
#!/bin/bash

# Disable Activities hot corner
gsettings set org.gnome.shell enable-hot-corners false

# Disable all keyboard shortcuts
KEYS=$(gsettings list-keys org.gnome.desktop.wm.keybindings)
for key in $KEYS; do
    gsettings set org.gnome.desktop.wm.keybindings "$key" "[]"
done

# Also disable some media/file shortcuts
KEYS=$(gsettings list-keys org.gnome.settings-daemon.plugins.media-keys)
for key in $KEYS; do
    gsettings set org.gnome.settings-daemon.plugins.media-keys "$key" "[]"
done

echo "All GNOME shortcuts disabled and hot corner removed."
EOF

# Set permissions
chmod +x "$DESKTOP_DIR/post.sh"
chown "$NEW_USER:$NEW_USER" "$DESKTOP_DIR/post.sh"

echo "post.sh has been placed on $NEW_USER's Desktop."

echo "[SUCCESS] User '$USERNAME' provisioned with shared folder '$SHARED_FOLDER'."
echo "[SUCCESS] Repo cloned to /home/$USERNAME/$REPO_NAME and dependencies installed."


