
set -e

TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
HOST_NAME=net.brunopaz.ulauncher.tabs.extension
rm "$TARGET_DIR/com.google.chrome.example.echo.json"

echo "Native messaging host $HOST_NAME has been uninstalled."
