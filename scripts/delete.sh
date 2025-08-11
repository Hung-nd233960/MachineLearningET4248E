#!/bin/bash

set -e

USERNAME="lockeddown"
SHARED_FOLDER="/shared"
GROUPNAME="sharedgroup"

# 1. Remove user and their home directory
if id "$USERNAME" >/dev/null 2>&1; then
    echo "[INFO] Deleting user '$USERNAME' and home directory..."
    userdel -r "$USERNAME"
else
    echo "[WARN] User '$USERNAME' does not exist."
fi

# 2. Remove shared folder
if [ -d "$SHARED_FOLDER" ]; then
    echo "[INFO] Removing shared folder '$SHARED_FOLDER'..."
    rm -rf "$SHARED_FOLDER"
else
    echo "[WARN] Shared folder '$SHARED_FOLDER' not found."
fi

# 3. Remove group if it exists and has no members
if getent group "$GROUPNAME" >/dev/null; then
    if [ "$(getent group "$GROUPNAME" | cut -d: -f4)" = "" ]; then
        echo "[INFO] Removing empty group '$GROUPNAME'..."
        groupdel "$GROUPNAME"
    else
        echo "[WARN] Group '$GROUPNAME' not empty, not deleting."
    fi
fi

echo "[SUCCESS] User, home directory, and shared folder removed."
