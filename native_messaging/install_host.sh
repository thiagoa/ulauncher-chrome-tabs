#!/bin/sh

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"

HOST_NAME=net.brunopaz.ulauncher.tabs.extension

# Create directory to store native messaging host.
mkdir -p "$TARGET_DIR"

# Copy native messaging host manifest.
cp "$DIR/$HOST_NAME.json" "$TARGET_DIR"

TARGET_FILE=$TARGET_DIR/$HOST_NAME.json

# Set permissions for the manifest so that all users can read it.
chmod o+r "$TARGET_FILE"
echo "Native messaging host $HOST_NAME has been installed into $TARGET_FILE"
