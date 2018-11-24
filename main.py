"""Ulauncher extension main  class"""

import logging
import json
import threading
import websocket
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

LOGGER = logging.getLogger(__name__)

MESSAGING_ACTION_GET_TABS = 'GET_TABS'
MESSAGING_ACTION_FOCUS_TAB = 'FOCUS_TAB'
MESSAGING_ACTION_PING = 'PING'
MESSAGING_ACTION_PONG = 'PONG'
HOST_WEBSOCKET_HOSTNAME = '127.0.0.1'
HOST_WEBSOCKET_PORT = '10200'
REFRESH_TABS_LIST_TIMER = 30  # Refresh opened tabs list every 30 seconds
# If connection is lost to web socket, try to reconnect after x seconds.
WEBSOCKET_RECONNECT_TIMER = 10


class ChromeTabsExtension(Extension):
    """ Main extension class """

    def __init__(self):
        """ init method """
        super(ChromeTabsExtension, self).__init__()

        LOGGER.info("Initializing Chrome Tabs extension")

        self.tabs = []

        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        # connect to the native host application via websocket
        self.connect_to_websocket()

    def get_tabs(self):
        """ Calls native host application via websockets to get a list of current opened tabs """

        try:
            self.ws.send(json.dumps({
                'action': MESSAGING_ACTION_GET_TABS
            }))
        except Exception as e:
            LOGGER.error('Failed to get tabs: %s' % e)
        finally:
            # Run this function periodically to get the updated list of tabs.
            time = threading.Timer(REFRESH_TABS_LIST_TIMER, self.get_tabs)
            time.start()

    def send_ws_message(self, message):
        """ Sends a message to Native host Websocket Server, handling all reconnects """
        self.ws.send(message)

    def connect_to_websocket(self):
        """ Connects to the websocket running on the native host application """

        self.ws = websocket.WebSocketApp(
            "ws://%s:%s" % (HOST_WEBSOCKET_HOSTNAME, HOST_WEBSOCKET_PORT),
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_open=self.on_ws_open,
            on_close=self.on_ws_close,
        )

        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()

    def on_ws_message(self, message):
        """ Function called when we receive a message from the websocket """
        LOGGER.info("Received message from websocket %s" % message)

        try:
            result = json.loads(message)

            if result['action'] == MESSAGING_ACTION_PING:
                self.send_ws_message(json.dumps({
                    'action': MESSAGING_ACTION_PONG
                }))

            if result['action'] == MESSAGING_ACTION_GET_TABS:
                if result['tabs']:
                    self.tabs = sorted(
                        result['tabs'], key=lambda k: k['name'])
                else:
                    self.tabs = []

        except ValueError:
            LOGGER.info(
                "Message received from websocket was not in a valid format")

    def on_ws_error(self, ws, error):
        """ Callback when we receive an error from the websocket """
        LOGGER.error("Websocket connection error: %s" % error)

        if ws is not None:
            ws.close()
            ws = None
            del ws

        time = threading.Timer(WEBSOCKET_RECONNECT_TIMER,
                               self.connect_to_websocket)
        time.start()

    def on_ws_close(self):
        """ Callback function that fires when the socket connection is closed """
        LOGGER.info("Closed connection to websocket")

    def on_ws_open(self):
        """ Callback when the websocket connection is opened """
        LOGGER.info("Opened websocket connection")

        # Get the current open tabs list.
        self.get_tabs()


class KeywordQueryEventListener(EventListener):
    """ Handles Keyboard input """

    def on_event(self, event, extension):
        """ Handles the event """
        items = []

        query = event.get_argument()
        if query is None:
            tabs = extension.tabs
        else:
            tabs = [t for t in extension.tabs if query.lower()
                    in t['name'].lower()]

        if not tabs:
            items.append(ExtensionResultItem(icon='images/icon.png',
                                             name='No tabs found',
                                             description='Make sure your ulauncher-tabs-helper chrome extension is installing and running',
                                             on_enter=HideWindowAction()))
        else:
            for tab in tabs[:25]:
                items.append(ExtensionSmallResultItem(icon='images/icon.png',
                                                      name=tab['name'].encode(
                                                          "utf-8"),
                                                      on_enter=ExtensionCustomAction(tab['id'])))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    """ Handles the click on an item. It will send a message to Chrome via the native host to focus the selected tab """

    def on_event(self, event, extension):
        tabId = event.get_data()

        extension.send_ws_message(json.dumps({
            'action': MESSAGING_ACTION_FOCUS_TAB,
            'tabId': tabId
        }))

        return DoNothingAction()


if __name__ == '__main__':
    ChromeTabsExtension().run()
