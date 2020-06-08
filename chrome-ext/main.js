/**
 * Main entrypoint for the extension.
 */

const NATIVE_MESSAGING_HOST_NAME = 'net.brunopaz.ulauncher.tabs.extension';
var conn = null;

/**
 * Connect to the Native host and register event handlers.
 */
function connect() {
  console.log("Connecting to native messaging host:" + NATIVE_MESSAGING_HOST_NAME)
  conn = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST_NAME);
  conn.onMessage.addListener(onNativeMessage);
  conn.onDisconnect.addListener(onDisconnected);
}

/**
 * Callback when the connection to the host is lost
 */
function onDisconnected() {
  console.error("Failed to connect to Native host: " + chrome.runtime.lastError.message);
  conn = null;
}

/**
 * Returns a list of tabs opened in all Chrome windows.
 * @returns Promise
 */
function getTabs() {

  return new Promise((resolve, reject) => {

    chrome.windows.getAll({
      'populate': true
    }, (windows) => {

      tabsList = []
      windows.forEach(window => {
        window.tabs.forEach(tab => {
          tabsList.push({
            'id': tab.id,
            'name': tab.title
          })
        });
      });

      resolve(tabsList);
    });

  });
}
/**
 * Called when receiving a message from the host application.
 * The message is a json object with an "action" key and optional parameters
 * Ex:
 *{
   "action": "GET_TABS"
 } {
   "action": "FOCUS_TAB",
   "tabId": 328
 }
 * @param {string} message
 */
function onNativeMessage(message) {
  message = JSON.parse(message);
  console.log("Received message from native host ", message.action);

  switch (message.action) {
    // Get list of tabs
    case "GET_TABS":
      getTabs().then((tabs) => {
        console.log("Sending tabs list to Native Host", tabs);
        conn.postMessage({
          action: "GET_TABS",
          tabs: tabs
        });
      });
      break;

      // focus tab
    case "FOCUS_TAB":
      console.log("Focusing tab with id:", message.tabId);
      chrome.tabs.get(message.tabId, (tab) => {
        chrome.windows.update(tab.windowId, {
          focused: true
        });
        chrome.tabs.update(tab.id, {
          active: true
        });
      });
      break;
    case "PONG":
      console.log("Pong received from native host");
      break;
    default:
      console.error("Unrecognized action");
  }
}

chrome.runtime.onInstalled.addListener(function () {
  console.log("The extension has been installed");
});


// Connect to the native host
connect();


// Refresh connection every minute
setInterval(() => {

  if (!conn) {
    console.log('No connection to native host. Reconnecting...');
    connect();
  }

  /*console.log('Sending ping message to Native Host')
  conn.postMessage({
    action: 'PING'
  });*/
}, 1000 * 60);
