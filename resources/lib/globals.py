# Everything that is to be globally accessible must be defined in this module.
# Using the Kodi reuseLanguageInvoker feature, only the code in the addon.py module will be run every time the addon is called,
# all other modules (imports) are initialized only on the first invocation of the add-on.

from urllib.parse import parse_qsl

import os
import xbmcaddon


class GlobalVariables(object):
    """Encapsulation for global variables to work around quirks with
    Kodi's reuseLanguageInvoker behavior"""
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=invalid-name, too-many-instance-attributes

    PLUGIN_URL = "plugin://plugin.video.rivedila7/"
    FANART_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'fanart.jpg')
    THUMB_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
    
    URL_BASE = "https://www.la7.it"
    URL_LIVE_LA7 = "https://www.la7play.it/dirette/la7"
    URL_LIVE_LA7CINEMA = "https://www.la7play.it/dirette/la7-cinema"
    URL_LIVE_LA7EVENTI = "https://www.la7play.it/live-eventi-la7"
    URL_MPD_LA7EVENTI = 'https://d15umi5iaezxgx.cloudfront.net/LA7FEED01/DRM/DASH/Live.mpd'
    URL_TGDIGITAL = "https://tg.la7.it/listing/tg-digital?page=0"
    URL_BASE_TGDIGITAL = "https://tg.la7.it"
    URL_PLAY_BASE = "https://www.la7play.it"
    URL_RIVEDILA7 = "https://www.la7play.it/guida-tv-rivedi/la7"
    URL_RIVEDILA7CINEMA = "https://www.la7play.it/guida-tv-rivedi/la7-cinema"
    URL_PROGRAMMI = "https://www.la7play.it/programmi"
    URL_TUTTI_PROGRAMMI = "https://www.la7play.it/programmi"
    URL_TECHE_LA7 = "https://www.la7play.it/programmi"
    URL_CERCA_LA7 = "https://www.la7play.it/ricerca?query="
    URL_FILM = "https://www.la7play.it/film"
    URL_DOCUMENTARI = "/documentari"

    # la7play.it persisted GraphQL queries (re-discover them with tools/browse.py --gql)
    GQL_QUERIES = {
        'allPrograms': 'f7034d55158fc906',
        'nodeReplica': '64b0309c926cd9f8',
        'playerSettingsReplica': 'a3db22fe0ebb31ce',
        'desktopLeafVideoBundle': '656f3c6b927a1a0c',
        'desktopLeafReplicaBundle': '022b8f4f2fb98d68',
        'desktopNodeBio': '23bed4d00e549922',
        'nsContentHub': '0f3f2c4225230faf',
        'contentSeoByPath': '66b5628df2976992',
        'siteSearch': '4da1e384f8a63808',
        'siteSearchSuggest': '647c199f01d967ce',
        # listing of a program page: the path is the node name, e.g. "otto e mezzo"
        'filteredNodeVideos': '6f384b6747f1a846',
        'filteredNodeVideosNextPage': 'fe69b4f8f4cbd498',
        'filteredNodeReplicas': 'e4ec45c8e38bb081',
        'filteredNodeReplicasNextPage': '58f48c68e20819bd',
        'filteredNodeVideosNextPage2': 'fe69b4f8f4cbd498',
        'nodePage': 'e9d39e6838f7f588',
        'nodeMenu': '4c25fdabd87a3720',
    }



    # DRM config
    DRM = 'com.widevine.alpha'
    DRM_PROTOCOL = 'mpd'
    KEY_WIDEVINE = "https://la7.prod.conax.cloud/widevine/license"

    # la7play.it player configuration (nodeConfigurazionePlayerRepliches node id 1)
    URL_CDN_VOD = "https://awsvodpkg.iltrovatore.it"
    URL_CDN_DRM = "https://d3iki3eydrtvsa.cloudfront.net"
    URL_DRM_TOKEN = "https://svc-01.la7play.it/DRM/tk.php"
    DRM_CONTENT_ID = "667"

    # Live channels: fixed DASH manifests on the DRM CDN, token keyed by content id
    URL_MPD_LIVE_LA7 = "https://d15umi5iaezxgx.cloudfront.net/LA7/DRM/DASH/Live.mpd"
    URL_MPD_LIVE_LA7CINEMA = "https://d15umi5iaezxgx.cloudfront.net/LA7D/DRM/DASH/Live.mpd"
    DRM_LIVE_ID_LA7 = "1"
    DRM_LIVE_ID_LA7CINEMA = "2"
    HEADERS_SET = {
        'host_license': 'la7.prod.conax.cloud',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'accept': '*/*',
        'accept-language': 'en,en-US;q=0.9,it;q=0.8',
        'dnt': '1',
        'te': 'trailers',
        'origin': 'https://www.la7.it',
        'referer': 'https://www.la7.it/',
    }

    def __init__(self):
        """Do nothing on constructing the object"""
        # The class initialization (GlobalVariables) will only take place at the first initialization of this module
        # on subsequent add-on invocations (invoked by reuseLanguageInvoker) will have no effect.
        # Define here only the variables necessary for the correct initialization of the other project modules
        self.IS_ADDON_FIRSTRUN = None
        self.ADDON = None
        self.ADDON_DATA_PATH = None
        self.DATA_PATH = None

    def init_globals(self, argv):
        """Initialized globally used module variables. Needs to be called at start of each plugin instance!"""
        # IS_ADDON_FIRSTRUN: specifies if the add-on has been initialized for the first time
        #                    (reuseLanguageInvoker not used yet)
        self.IS_ADDON_FIRSTRUN = self.IS_ADDON_FIRSTRUN is None
        # xbmcaddon.Addon must be created at every instance otherwise it does not read any new changes to the settings
        self.ADDON = xbmcaddon.Addon()
        self.LANGUAGE = self.ADDON.getLocalizedString
        self.PARAMS = parameters_string_to_dict(argv[2])
        self.MODE = str(G.PARAMS.get("mode", ""))
        self.GIORNO = str(G.PARAMS.get("giorno", ""))
        self.LINK = str(G.PARAMS.get("link", ""))
        self.TITOLO = str(G.PARAMS.get("titolo", ""))
        self.THUMB = str(G.PARAMS.get("thumb", ""))
        self.PLOT = str(G.PARAMS.get("plot", ""))
        self.PLAY = str(G.PARAMS.get("play", ""))
        self.PAGENUM = 0
        self.LIST_PROGRAMMI = []

        if self.IS_ADDON_FIRSTRUN:
            # Global variables that do NOT need to be updated at every addon run
            self.ADDON_ID = self.ADDON.getAddonInfo('id')
            self.PLUGIN_NAME = self.ADDON.getAddonInfo('name')
            self.ICON = self.ADDON.getAddonInfo('icon')
            self.ADDON_DATA_PATH = self.ADDON.getAddonInfo('path')  # Add-on folder
            self.DATA_PATH = self.ADDON.getAddonInfo('profile')  # Add-on user data folder
            self.PLUGIN_HANDLE = int(argv[1])


def parameters_string_to_dict(parameters):
    # xbmc.log('PARAMETERS------: '+str(parameters),xbmc.LOGINFO)
    param_dict = dict(parse_qsl(parameters[1:]))
    return param_dict


# We initialize an instance importable of GlobalVariables from run_addon.py,
# where G.init_globals() MUST be called in the addon entry point.
G = GlobalVariables()
