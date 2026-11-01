import base64
import datetime
import json
import os
import sys
import time
import re
import requests
import inputstreamhelper

import urllib.parse
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import xbmc
import xbmcgui
import xbmcplugin

from bs4 import BeautifulSoup
from resources.lib.globals import G


def show_root_menu():
    xbmcgui.Window(10000).clearProperty('la7_search_url')

    """ Show the plugin root menu """
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32002) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32009) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7cinema.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7cinema"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32001) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'rivedila7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32004) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7cinema.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7cinema"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32010) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'la7prime.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "la7_prime"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32006) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'programmi.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "tutti_programmi"}, li_style)
    li_style = xbmcgui.ListItem('[B]Documentari[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'film.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "documentari"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32012) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'cerca.png'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "cerca_la7"}, li_style)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def add_directory_item_nodup(parameters, li, title='', folder=True, is_live=False):
    if not title:
        title = G.TITOLO
    if title in G.LIST_PROGRAMMI:
        # xbmc.log('PROGRAMMA DUPLICATO', xbmc.LOGINFO)
        pass
    else:
        url = G.PLUGIN_URL + '?' + urllib.parse.urlencode(parameters)
        if is_live:
            url += '&_l=.pvr'  # disabilita per le dirette la richiesta di riprendere il video dall'ultima volta
        # xbmc.log('LIST------: '+str(url),xbmc.LOGINFO)
        if not folder:
            li.setInfo('video', {})
            li.setProperty('isPlayable', 'true')
        return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)


def play_dirette(url, live):
    xbmc.log('PLAY DIRETTE', xbmc.LOGINFO)
    #xbmc.log('PAGE DIRETTE-----: '+str(url),xbmc.LOGINFO)

    url_title = ''
    regex5 = ''
    titolo_diretta = ''

    if live:
        if url == G.URL_LIVE_LA7:
            url_title = G.URL_BASE
            regex5 = r'var orainonda = ".*\t(.*?)"'
        elif url == G.URL_LIVE_LA7CINEMA:
            url_title = G.URL_BASE
            regex5 = r'var orainondala7d = ".*\t(.*?)"'
        elif url == G.URL_LIVE_LA7EVENTI:
            url_title = G.URL_LIVE_LA7EVENTI
        #xbmc.log('URL TITLE-----: '+str(url_title),xbmc.LOGINFO)

        req = Request(url_title, headers={'user-agent': G.HEADERS_SET['user-agent']})
        page = urlopen(req).read()
        html = page.decode(errors='replace')
        #xbmc.log('REGEX5-----: '+str(re.findall(regex5, html)),xbmc.LOGINFO)
        
        if url == G.URL_LIVE_LA7EVENTI:
            titolo_diretta = 'LA7 Eventi Live'
        else:
            titolo_diretta = re.findall(regex5, html)[0]
        #xbmc.log('TITOLO DIRETTA-----: '+str(titolo_diretta),xbmc.LOGINFO)

    response = requests.get(url, headers={'user-agent': G.HEADERS_SET['user-agent']}, verify=False).content.decode()
    try:
        preurl = re.findall('preTokenUrl = "(.+?)"', response)[0]
    except Exception as e:
        e = sys.exc_info()[0]
        xbmc.log('EXCEP PREURL: ' + str(e), xbmc.LOGINFO)
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
        return
    response = response.replace("\'", '"')

    if url == G.URL_LIVE_LA7EVENTI:
        mpdurl = G.URL_MPD_LA7EVENTI
    else:
        mpdurl = re.findall('dash.+?"(.+?)"', response, re.DOTALL)[0]
    #xbmc.log('URL VIDEO MPD-----: '+str(mpdurl),xbmc.LOGINFO)

    play_drm(mpdurl, preurl, titolo_diretta, titolo_diretta)


def play_drm(mpdurl, preurl, titolo='', plot=''):
    """ Play a Widevine protected DASH stream through the conax license server """
    headers_tok = {
        # 'host' is deliberately not set: the pre-authorization endpoint derives it from
        # its own URL (the old pat.la7.it value made tk.php answer with an empty body)
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'dnt': G.HEADERS_SET['dnt'],
        'te': G.HEADERS_SET['te'],
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    try:
        response = requests.get(preurl, headers=headers_tok, verify=False).json()
        pre_auth_token = response['preAuthToken']
    except Exception as exc:
        xbmc.log('RivediLA7: DRM token request failed (%s)' % exc, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
        return

    headers_lic = {
        'host': G.HEADERS_SET['host_license'],
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'preAuthorization': pre_auth_token,
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    pre_lic = '&'.join(['%s=%s' % (name, value) for (name, value) in headers_lic.items()])
    # xbmc.log('LICENSE1------: '+str(pre_lic),xbmc.LOGINFO)

    tsatmp = str(int(time.time()))
    license_url = G.KEY_WIDEVINE + '?d=%s' % tsatmp
    lic_url = '%s|%s|R{SSM}|' % (license_url, pre_lic)
    # xbmc.log('LICENSE2------: '+str(lic_url),xbmc.LOGINFO)
    is_helper = inputstreamhelper.Helper(G.DRM_PROTOCOL, drm=G.DRM)
    if is_helper.check_inputstream():
        listitem = xbmcgui.ListItem(titolo or G.TITOLO, offscreen=True)
        listitem.setPath(mpdurl)
        listitem.setInfo('video', {'plot': plot or G.PLOT, 'title': titolo or G.TITOLO})
        listitem.setProperty("inputstream", is_helper.inputstream_addon)
        listitem.setProperty("inputstream.adaptive.manifest_type", G.DRM_PROTOCOL)
        listitem.setProperty("inputstream.adaptive.license_type", G.DRM)
        listitem.setProperty("inputstream.adaptive.license_key", lic_url)
        listitem.setMimeType('application/dash+xml')
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)
    else:
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)


# la7play.it helpers: since the 2026 restyling la7.it redirects every content page
# to la7play.it, a Next.js application. The old Drupal markup is gone: the schedule
# and the player data are only available inside the React Server Components payload
# embedded in each page.
RSC_PUSH = 'self.__next_f.push('

GIORNI_SETTIMANA = ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica']
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
        'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']


def fetch_page(url):
    """ Download a page and return its decoded HTML """
    req = Request(url, headers={'user-agent': G.HEADERS_SET['user-agent']})
    return urlopen(req, timeout=30).read().decode('utf-8', 'replace')


def rsc_payload(html):
    """ Concatenate the React Server Components payloads embedded in a la7play.it page """
    payload = []
    pos = 0
    while True:
        pos = html.find(RSC_PUSH, pos)
        if pos < 0:
            return ''.join(payload)
        start = pos + len(RSC_PUSH)
        depth = 0
        in_string = False
        escaped = False
        end = start
        while end < len(html):
            char = html[end]
            if in_string:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    break
            end += 1
        try:
            chunk = json.loads(html[start:end + 1])
        except ValueError:
            chunk = []
        if len(chunk) > 1 and isinstance(chunk[1], str):
            payload.append(chunk[1])
        pos = end


def rsc_value(payload, key):
    """ Return the JSON value of the first "key": value pair found in the payload """
    pos = payload.find('"%s":' % key)
    if pos < 0:
        return None
    start = pos + len(key) + 3
    while start < len(payload) and payload[start] in ' \t':
        start += 1
    depth = 0
    in_string = False
    escaped = False
    end = start
    while end < len(payload):
        char = payload[end]
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in '[{':
            depth += 1
        elif char in ']}':
            depth -= 1
            if depth == 0:
                break
        elif char in ',}' and depth == 0:
            break
        end += 1
    try:
        return json.loads(payload[start:end + 1])
    except ValueError:
        return None


def guida_tv_giorni(url):
    """ Return the days of a guida-tv-rivedi page, oldest first """
    giorni = rsc_value(rsc_payload(fetch_page(url)), 'giorno') or []
    result = []
    for giorno in giorni:
        data = (giorno.get('@attributes') or {}).get('data')
        if data:
            result.append({'data': data, 'programma': giorno.get('programma') or []})
    return result


def guida_tv_url():
    """ guida-tv-rivedi page of the channel currently selected in the add-on """
    if G.MODE == 'rivedi_la7cinema':
        return G.URL_RIVEDILA7CINEMA
    return G.URL_RIVEDILA7


def giorno_label(data):
    """ '01-11-2026' -> 'domenica 1 novembre' """
    try:
        day, month, year = [int(part) for part in data.split('-')]
        date = datetime.date(year, month, day)
    except (AttributeError, TypeError, ValueError):
        return data
    return '%s %d %s' % (GIORNI_SETTIMANA[date.weekday()], date.day, MESI[date.month - 1])


class GqlError(Exception):
    """ A la7play.it query failed, the site probably changed its query ids """


def gql_hash(name):
    """ Persisted query id of a la7play.it GraphQL query """
    return G.GQL_QUERIES[name]


def gql(name, variables=None):
    """ Run a persisted la7play.it query and return its data object """
    url = '%s/api/gql/%s' % (G.URL_PLAY_BASE, gql_hash(name))
    if variables is not None:
        # the variables travel as sorted, unpadded base64url JSON
        encoded = json.dumps(variables, separators=(',', ':'), sort_keys=True).encode('utf-8')
        url += '/' + base64.urlsafe_b64encode(encoded).decode('utf-8').rstrip('=')
    headers = {'user-agent': G.HEADERS_SET['user-agent'], 'accept': 'application/json',
               'referer': G.URL_PLAY_BASE + '/'}
    try:
        data = requests.get(url, headers=headers, timeout=30).json()
    except Exception as exc:
        raise GqlError('%s (%s)' % (name, exc))
    if not isinstance(data, dict) or 'data' not in data:
        raise GqlError('%s returned no data' % name)
    return data['data']


def la7play_programmi():
    """ List the programs published by the la7play.it index """
    programmi = gql('allPrograms').get('graphqlTuttiProgrammi', {}).get('results') or []
    for programma in programmi:
        titolo = (programma.get('titolo') or '').strip()
        pathname = programma.get('pathname') or ''
        if not titolo or not pathname:
            continue
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        art = {'fanart': G.FANART_PATH}
        if programma.get('img'):
            art['thumb'] = programma['img']
        liStyle.setArt(art)
        if programma.get('occhiello'):
            liStyle.setInfo('video', {'plot': programma['occhiello'].strip()})
        add_directory_item_nodup({"mode": G.MODE, "link": G.URL_PLAY_BASE + pathname}, liStyle, titolo)
    xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def la7play_repliche(pathname):
    """ List the replays of a program from the guida TV of the last week """
    added = 0
    seen = set()
    for url in (G.URL_RIVEDILA7, G.URL_RIVEDILA7CINEMA):
        for giorno in guida_tv_giorni(url):
            for prog in giorno['programma']:
                path = prog.get('pathname') or ''
                # a program owns its episodes, not the ones of a similarly named one
                if not path.startswith(pathname.rstrip('/') + '/') or path in seen:
                    continue
                seen.add(path)
                titolo = (prog.get('titolo') or '').strip()
                plot = (prog.get('sinossi') or '').strip()
                liStyle = xbmcgui.ListItem(giorno_label(giorno['data']) + ' ' + titolo, offscreen=True)
                art = {'fanart': G.FANART_PATH}
                thumb = prog.get('immagine_programma') or prog.get('immagine_scena') or ''
                if thumb:
                    art['thumb'] = thumb
                liStyle.setArt(art)
                liStyle.setInfo('video', {'plot': plot})
                liStyle.setProperty('isPlayable', 'true')
                parameters = {"mode": G.MODE, "play": G.URL_PLAY_BASE + path,
                              "titolo": titolo, "thumb": thumb, "plot": plot}
                url2 = G.PLUGIN_URL + '?' + urllib.parse.urlencode(parameters)
                xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url2, listitem=liStyle, isFolder=False)
                added += 1
    return added


def la7play_nodes(url):
    """ Content nodes (a path plus a title) published in a la7play.it page """
    nodes = []
    seen = set()

    def walk(value):
        if isinstance(value, dict):
            path = value.get('path') or value.get('pathname')
            title = value.get('titolo') or value.get('title') or value.get('nome')
            if (isinstance(path, str) and path.startswith('/') and isinstance(title, str)
                    and title and path not in seen):
                seen.add(path)
                nodes.append(value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for line in rsc_payload(fetch_page(url)).split('\n'):
        try:
            walk(json.loads(re.sub(r'^[0-9a-f]+:', '', line)))
        except ValueError:
            continue
    return nodes


def content_nodes(value, nodes=None):
    """ Collect the content nodes of an already decoded payload """
    if nodes is None:
        nodes = []
    if isinstance(value, dict):
        path = value.get('path') or value.get('pathname')
        title = value.get('titolo') or value.get('title') or value.get('nome')
        known = set(node.get('path') or node.get('pathname') for node in nodes)
        if (isinstance(path, str) and path.startswith('/') and isinstance(title, str)
                and title and path not in known):
            nodes.append(value)
        for item in value.values():
            content_nodes(item, nodes)
    elif isinstance(value, list):
        for item in value:
            content_nodes(item, nodes)
    return nodes


def la7play_list(url):
    """ List the content nodes of a la7play.it page, folders or playable items """
    la7play_emit(la7play_nodes(url))


def la7play_hub(path):
    """ List the contents of a la7play.it hub page, e.g. /documentari """
    route = gql('nsContentHub', {'path': path}).get('route') or {}
    la7play_emit(content_nodes(route.get('entity') or {}))


def documentari():
    """ Show the Documentari section """
    if G.LINK != "":
        la7play_list(G.LINK)
        return
    la7play_hub(G.URL_DOCUMENTARI)


def la7play_emit(nodes):
    for node in nodes:
        path = node.get('path') or node.get('pathname')
        titolo = (node.get('titolo') or node.get('title') or node.get('nome') or '').strip()
        plot = (node.get('sinossi') or node.get('sinossibreve') or node.get('description') or '').strip()
        thumb = node.get('coverImage') or node.get('smartTvLocandina') or ''
        upload = node.get('uploadVideo') or {}
        playable = bool(upload.get('cf_remote_url')) or '/puntate/' in path or path.startswith('/film/')
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        art = {'fanart': G.FANART_PATH}
        if isinstance(thumb, str) and thumb.startswith('http'):
            art['thumb'] = thumb
        liStyle.setArt(art)
        if plot:
            liStyle.setInfo('video', {'plot': plot})
        if playable:
            liStyle.setProperty('isPlayable', 'true')
            parameters = {"mode": G.MODE, "play": G.URL_PLAY_BASE + path, "titolo": titolo, "plot": plot}
            url2 = G.PLUGIN_URL + '?' + urllib.parse.urlencode(parameters)
            xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url2, listitem=liStyle, isFolder=False)
        else:
            add_directory_item_nodup({"mode": G.MODE, "link": G.URL_PLAY_BASE + path}, liStyle, titolo)
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def video_link(video):
    """ Playable URL of a la7play.it node (NodeReplica/NodeVideo/NodeEventoSingolo),
    returned together with a flag telling whether the stream is DRM protected """
    if not video:
        return '', False
    if video.get('urlVideo'):
        return video['urlVideo'], False
    upload = video.get('uploadVideo') or {}
    remote = upload.get('cf_remote_url') or ''
    if not remote:
        return '', False
    if video.get('drm'):
        # Encrypted content is published as a single DASH stream on the DRM CDN
        name = remote.lstrip('/').split('/')[-1]
        return '%s/%s/DASH/%s.mpd' % (G.URL_CDN_DRM.rstrip('/'), name, name), True
    # Clear content is published as a Kaltura urlset of progressive MP4 renditions:
    # strip the .mp4 suffix and let the CDN build the HLS playlist on the fly
    paths = remote if remote.startswith('/') else '/' + remote
    paths = paths.replace('.mp4', '')
    if not upload.get('cf_old_entry_id'):
        entries = []
        for entry in paths.split(','):
            entry = entry.strip()
            if not entry or entry.startswith('/nk/'):
                entries.append(entry)
            elif entry.startswith('/'):
                entries.append('/nk' + entry)
            else:
                entries.append('/nk/' + entry)
        paths = ','.join(entries)
    return '%s/local/hls/,%s,.mp4.urlset/master.m3u8' % (G.URL_CDN_VOD.rstrip('/'), paths), False


def drm_token_url():
    """ VOD pre-authorization token URL used by the la7play player """
    return '%s?id=%s&contentType=VOD&v=%d' % (G.URL_DRM_TOKEN, G.DRM_CONTENT_ID, int(time.time() * 1000))


def play_video(page_video, live):
    xbmc.log('PLAY VIDEO', xbmc.LOGINFO)
    if live:
        return

    try:
        html = fetch_page(page_video)
    except Exception as exc:
        xbmc.log('RivediLA7: unable to load %s (%s)' % (page_video, exc), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
        return

    link_video, is_drm = video_link(rsc_value(rsc_payload(html), 'videoData'))

    if not link_video:
        # Pages not served by la7play.it still embed a plain mp4/HLS link
        found = re.findall(r'\.net/i/.*?content/(.*?)(?:\.mp4)', html)
        found_m3u8 = re.findall('m3u8: "(.*?)"', html)
        found_mp4 = re.findall(r'mp4["\']?\s*:\s*["\'](https?://[^"\']+\.mp4)["\']', html)
        if found:
            link_video = G.URL_CDN_VOD + '/local/hls/,/content/' + found[0] + '.mp4.urlset/master.m3u8'
        elif found_m3u8:
            link_video = found_m3u8[0]
        elif found_mp4:
            link_video = found_mp4[0]
        elif 'preTokenUrl = "' in html:
            play_dirette(page_video, False)
            return

    listitem = xbmcgui.ListItem(G.TITOLO, offscreen=True)
    listitem.setInfo('video', {'title': G.TITOLO, 'plot': G.PLOT})
    if G.THUMB != "":
        listitem.setArt({'thumb': G.THUMB})
    if not link_video:
        xbmc.log('RivediLA7: NO VIDEO LINK', xbmc.LOGINFO)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, False, listitem)
        return

    if is_drm:
        play_drm(link_video, drm_token_url())
        return

    # Clear HLS streams are played by Kodi itself: inputstream.adaptive is only
    # needed for the Widevine protected DASH streams
    listitem.setPath(link_video)
    xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)


def rivedi(url, thumb):
    """ List the replayable days of the channel guida TV """
    try:
        giorni = guida_tv_giorni(url)
    except Exception as exc:
        xbmc.log('RivediLA7: unable to load %s (%s)' % (url, exc), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    # Only days that still have at least one replayable program are listed
    giorni = [giorno for giorno in giorni if any(prog.get('pathname') for prog in giorno['programma'])]
    if not giorni:
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    for giorno in reversed(giorni):
        liStyle = xbmcgui.ListItem(giorno_label(giorno['data']), offscreen=True)
        liStyle.setArt({'thumb': os.path.join(G.THUMB_PATH, thumb), 'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "giorno": giorno['data']}, liStyle)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def rivedi_giorno():
    """ List the replayable programs of the selected day """
    try:
        giorni = guida_tv_giorni(guida_tv_url())
    except Exception as exc:
        xbmc.log('RivediLA7: unable to load the guida TV (%s)' % exc, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    giorno = next((item for item in giorni if item['data'] == G.GIORNO), None)
    if giorno is None:
        xbmc.log('RivediLA7: day %s not found in the guida TV' % G.GIORNO, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    for prog in giorno['programma']:
        pathname = prog.get('pathname')
        if not pathname:
            continue
        orario = (prog.get('ora') or '').strip()
        nome = (prog.get('titolo') or '').strip()
        thumb = prog.get('immagine_programma') or prog.get('immagine_scena') or ''
        plot = (prog.get('sinossi') or '').strip()
        liStyle = xbmcgui.ListItem(orario + " " + nome, offscreen=True)
        art = {'fanart': G.FANART_PATH}
        if thumb:
            art['thumb'] = thumb
        liStyle.setArt(art)
        liStyle.setInfo('video', {'plot': plot})
        liStyle.setProperty('isPlayable', 'true')
        parameters = {"mode": G.MODE, "play": G.URL_PLAY_BASE + pathname, "titolo": nome, "thumb": thumb, "plot": plot}
        url2 = G.PLUGIN_URL + '?' + urllib.parse.urlencode(parameters)
        xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url2, listitem=liStyle, isFolder=False)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def process_program_data(dati, config):
    if dati.find('a') is None:
        return
    url_trovato = dati.a.get('href').strip()
    # xbmc.log('URL--------: '+str(url_trovato),xbmc.LOGINFO)
    if url_trovato not in config['exclusions']:
        url_trovato = config['mappings'].get(url_trovato, url_trovato)
        titolo = ''
        if dati.find('div', class_='titolo'):
            titolo = dati.find('div', class_='titolo').text.strip()
        if titolo == '':
            titolo = url_trovato.lstrip('/').replace('-', ' ').upper()
        # xbmc.log('TITLE1-----: '+str(titolo),xbmc.LOGINFO)
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        link = G.URL_BASE + url_trovato
        # xbmc.log('LINK-----: '+str(link),xbmc.LOGINFO)
        if len(dati) > 0:
            try:
                thumb = dati.find('div', class_='image-bg lozad').get('data-background-image')
            except Exception as e:
                e = sys.exc_info()[0]
                xbmc.log('EXCEP THUMB1: ' + str(e), xbmc.LOGINFO)
                thumb = ''
            if thumb:
                liStyle.setArt({'thumb': thumb})
            else:
                xbmc.log('NO THUMB1', xbmc.LOGINFO)
        liStyle.setArt({'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

        if titolo not in G.LIST_PROGRAMMI:
            G.LIST_PROGRAMMI.append(titolo)


def programmi_lettera():
    la7play_programmi()
    return

    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        
    #if programmi or tutti_programmi:
    if programmi or tutti_programmi:
        for dati in programmi:
            process_program_data(dati, config)

        for dati in tutti_programmi:
            process_program_data(dati, config)

        # Prog aggiunti manualmente
        programmi = {
            'LA MALA EDUCAXXXION 2': {
                'url': '/la-mala-educaxxxion',
                'img': 'https://kdam.iltrovatore.it/p/103/sp/10300/thumbnail/entry_id/0_j0z82ps2/version/100001/type/5/width/600/height/360/quality/100/name/0_j0z82ps2.jpg'
            },
        }
        for programma, program_info in programmi.items():
            titolo = programma
            liStyle = xbmcgui.ListItem(titolo, offscreen=True)
            url_trovato = program_info['url']
            link = G.URL_BASE + url_trovato
            thumb = program_info['img']
            liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
            add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

        xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_la7prime():
    titolo = 'Tutti i Film'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = G.URL_FILM
    thumb = os.path.join(G.THUMB_PATH, 'film.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_lettera_teche_la7():
    req_teche = Request(G.URL_TECHE_LA7, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page_teche = urlopen(req_teche)
    html_teche = BeautifulSoup(page_teche, 'html.parser')
    
    teche_la7 = html_teche.find_all('div', class_='list-item')

    if teche_la7:
        for dati in teche_la7:
            if not dati.find('a'):
                continue
            
            titolo_div = dati.find('div', class_='titolo')
            if titolo_div:
                nomicognomi = titolo_div.text.strip()
                cognominomi = " ".join(reversed(nomicognomi.split(" ")))
                
                url_trovato = dati.a.get('href').strip()
                bio_link = G.URL_BASE + url_trovato

                liStyle = xbmcgui.ListItem(cognominomi)
                
                video_info_tag = liStyle.getVideoInfoTag()
                video_info_tag.setTitle(cognominomi)
                
                thumb = ''
                try:
                    thumb_div = dati.find('div', class_='image-bg lozad')
                    if thumb_div and thumb_div.has_attr('data-background-image'):
                        thumb = thumb_div.get('data-background-image')
                except Exception:
                    pass
                
                if thumb:
                    liStyle.setArt({'thumb': thumb})
                
                liStyle.setArt({'fanart': G.FANART_PATH})
                
                add_directory_item_nodup({"mode": G.MODE, "link": bio_link}, liStyle, cognominomi)

        xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def mostra_biografia():
    plot = "Biografia non disponibile."
    titolo = "Biografia"
    try:
        req_bio = Request(G.LINK, headers={'user-agent': G.HEADERS_SET['user-agent']})
        page_bio = urlopen(req_bio)
        html_bio = BeautifulSoup(page_bio, 'html.parser')

        bio_element = html_bio.find('div', class_='field-name-field-biografia')
        if bio_element:
            plot = ' '.join(bio_element.text.split()).strip()

        titolo_element = html_bio.find('h1') or html_bio.find('div', class_='titolo')
        if titolo_element:
            titolo = titolo_element.text.strip()

    except Exception as e:
        xbmc.log(f'ERRORE ESTRAZIONE BIOGRAFIA da {G.LINK}: {str(e)}', xbmc.LOGWARNING)
        plot = f"Errore durante il caricamento: {str(e)}"

    xbmcgui.Dialog().textviewer(titolo, plot)
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)


def programmi_lettera_tg_meteo():
    titolo = 'TG LA7'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/tgla7'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'tgla7.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'TG Digital'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = G.URL_TGDIGITAL
    thumb = os.path.join(G.THUMB_PATH, 'tgdigital.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Edicola'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/omnibus-edicola'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'omnibusnews.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Omnibus Meteo'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/omnibus-meteo'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'omnibusmeteo.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Meteo della Sera'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/meteo-della-sera'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'meteodellasera.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def cerca_la7():
    window = xbmcgui.Window(10000)
    url = G.LINK

    # Se un video è appena terminato (Stop), riusa la ricerca salvata senza riaprire la tastiera
    era_in_video = window.getProperty('la7_video_in_corso') == '1'
    window.clearProperty('la7_video_in_corso')

    if era_in_video:
        url = window.getProperty('la7_search_url')

    # Se non c'è URL (nuova ricerca dal menu principale), apre la tastiera
    if not url:
        tastiera = xbmcgui.Dialog()
        testo = tastiera.input("Ricerca nel sito", type=xbmcgui.INPUT_ALPHANUM)
        if not testo:
            xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
            return
        query = quote_plus(testo)
        url = f"{G.URL_CERCA_LA7}{query}"
        window.setProperty('la7_search_url', url)
    else:
        window.setProperty('la7_search_url', url)

    try:
        req = Request(url, headers={'user-agent': G.HEADERS_SET['user-agent']})
        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
    except Exception as e:
        xbmc.log(f'ERRORE RICERCA LA7: {str(e)}', xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    rows = soup.find_all('div', class_=lambda c: c and 'views-row' in c)

    # Se non trova risultati: notifica e riapre subito la tastiera
    if not rows:
        xbmcgui.Dialog().notification("Cerca La7", "La ricerca non ha prodotto risultati", xbmcgui.NOTIFICATION_INFO, 3000)
        window.clearProperty('la7_search_url')
        G.LINK = ""
        cerca_la7()
        return

    # Elenco dei video trovati
    for row in rows:
        a_tag = row.find('a')
        if not a_tag or not a_tag.get('href'):
            continue

        href = a_tag.get('href').strip()
        video_link = G.URL_BASE + href

        title_div = row.find('div', class_='title')
        titolo = title_div.text.strip() if title_div else "Senza titolo"

        prop_div = row.find('div', class_='property')
        programma = prop_div.text.strip() if prop_div else ""

        data_div = row.find('div', class_='data')
        data_str = data_div.text.strip() if data_div else ""

        label = f"[{data_str}] {titolo}" if data_str else titolo

        thumb = ''
        thumb_div = row.find('div', class_='bg-img')
        if thumb_div and thumb_div.has_attr('data-background-image'):
            thumb = thumb_div.get('data-background-image').strip()
            if thumb.startswith('//'):
                thumb = 'https:' + thumb

        liStyle = xbmcgui.ListItem(label)
        video_info_tag = liStyle.getVideoInfoTag()
        video_info_tag.setTitle(label)
        if programma or data_str:
            video_info_tag.setPlot(f"{programma} - {data_str}".strip(" -"))

        if thumb:
            liStyle.setArt({'thumb': thumb, 'poster': thumb})
        liStyle.setArt({'fanart': G.FANART_PATH})

        add_directory_item_nodup({"mode": "cerca_la7", "play": video_link}, liStyle, label, folder=False)

    # Paginazione in fondo
    next_li = soup.find('li', class_='pager-next')
    if next_li and next_li.find('a'):
        next_url = G.URL_BASE + next_li.a.get('href').strip()
        li_next = xbmcgui.ListItem(">> Pagina Successiva")
        li_next.setArt({'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": "cerca_la7", "link": next_url}, li_next, ">> Pagina Successiva", folder=True)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


# PAGINA PRINCIPALE
# esempio https://www.la7.it/tgla7 (senza "/rivedila7")
def video_programma_landpage():
    # xbmc.log('LINK GLOBAL_LAND------: '+str(G.LINK),xbmc.LOGINFO)

    # ///// HOME /////
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'HOME' + "[/COLOR][/B]", offscreen=True))

    if G.LINK == G.URL_BASE + '/faccia-a-faccia':
        link_landpage = G.URL_BASE + '/facciaafaccia'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/boss-dei-comici':
        link_landpage = G.URL_BASE + '/il-boss-dei-comici'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/laria-destate':
        link_landpage = G.URL_BASE + '/lariadestate'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/tagada-doc':
        link_landpage = G.URL_BASE + '/taga-doc'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    else:
        req = Request(G.LINK, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html.parser')

    # VIDEO INIZIALE
    video_iniziale = html.find('div', class_='ultima_puntata')
    #xbmc.log('DATI VIDEO INIZIALE------: '+str(video_iniziale),xbmc.LOGINFO)
    if video_iniziale:
        get_rows_video_landpage_preview(video_iniziale)

    # PUNTATE    
    if (html.findAll(text="puntate")) or (html.findAll(text="Guarda ora")) or (html.findAll(text="Tutti i film")):
        # xbmc.log('TEST------: '+str(html.find('div',class_='home-block__content-inner')),xbmc.LOGINFO)
        video_puntate_1r = html.find('div', class_='home-block__content-inner').select('div[class="item"]')
        video_puntate_2r = html.find('section', class_='home-block home-block--oggi-striscia home-block--fixed').find_all('div', class_='item')
        # xbmc.log('TEST------: '+str(video_puntate_2r),xbmc.LOGINFO)
        if video_puntate_1r:
            get_rows_video_landpage(video_puntate_1r)
        if video_puntate_2r:
            get_rows_video_landpage(video_puntate_2r)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')


# PAGINA SECONDARIA
# esempio https://www.la7.it/tgla7/rivedila7 (con "/rivedila7")
def video_programma():
    page = ''
    first = None

    # la7play.it pages carry the whole content list in the page payload
    if G.LINK.startswith(G.URL_PLAY_BASE):
        pathname = G.LINK[len(G.URL_PLAY_BASE):].rstrip('/')
        if la7play_repliche(pathname):
            xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)
            return
        la7play_list(G.LINK)
        return

    #xbmc.log('PAGENUM------: '+str(G.PAGENUM),xbmc.LOGINFO)
    if (G.PAGENUM == 0):
        video_programma_landpage()

    if G.LINK != G.URL_TGDIGITAL:
        #xbmc.log('LINK GLOBAL------: '+str(G.LINK),xbmc.LOGINFO)
        req = Request(G.LINK + "/rivedila7", headers={'user-agent': G.HEADERS_SET['user-agent']})
        try:
            page = urlopen(req)
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP URL PAGINA SECONDARIA: ' + str(e), xbmc.LOGINFO)
            if xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005)):
                xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
                return
        html = BeautifulSoup(page, 'html.parser')

        # ///// SETTIMANA /////
        if G.PAGENUM == 0:
            xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'SETTIMANA' + "[/COLOR][/B]", offscreen=True))

            # FIRST VIDEO
            if html.find('div', class_='ultima_puntata'):
                first = html.find('div', class_='ultima_puntata')
            elif html.find('div', class_='contenitoreUltimaReplicaLa7d'):
                first = html.find('div', class_='contenitoreUltimaReplicaLa7d')
            elif html.find('div', class_='contenitoreUltimaReplicaNoLuminosa'):
                first = html.find('div', class_='contenitoreUltimaReplicaNoLuminosa')
            else:
                xbmc.log('NO FIRST VIDEO', xbmc.LOGINFO)
                if xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005)):
                    xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
                    return
            titolo = first.find('div', class_='title_puntata').text.strip()
            # xbmc.log('FIRST VIDEO----: '+str(titolo),xbmc.LOGINFO)
            first_video(first, titolo, True)

            # WEEK VIDEO
            if html.findAll(text=" LA SETTIMANA"):
                video_settimana = html.find('div', class_='home-block__content-carousel container-vetrina').find_all('div', class_='item')
                # xbmc.log('LA SETTIMANA----: '+str(video_settimana),xbmc.LOGINFO)
                if video_settimana:
                    get_rows_video(video_settimana)
            else:
                xbmc.log('NO WEEK VIDEO', xbmc.LOGINFO)

        # ///// ARCHIVIO /////
        if (html.findAll(text="Puntate Cult")) or (html.findAll(text="Tutti i film")):
            xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'ARCHIVIO' + "[/COLOR][/B]", offscreen=True))
            
            if (G.LINK == G.URL_BASE + '/chi-sceglie-la-seconda-casa') or (G.LINK == G.URL_BASE + '/lingrediente-perfetto') or (G.LINK == G.URL_BASE + '/una-giornata-particolare'):
                req2 = Request(G.LINK + "/rivedila7", headers={'user-agent': G.HEADERS_SET['user-agent']})
            else:
                req2 = Request(G.LINK + "/rivedila7/archivio?page=" + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
            page2 = urlopen(req2)
            html2 = BeautifulSoup(page2, 'html.parser')
            video_archivio = html2.find('div', class_='view-content clearfix').find_all('div', class_='views-row')
            if video_archivio:
                get_rows_video(video_archivio)
                page = html2.find('li', class_='pager-next')
                pagenext(page)
        else:
            xbmc.log('NO ARCHIVIO VIDEO', xbmc.LOGINFO)

    # TG DIGITAL
    else:
        req = Request(G.LINK + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
        #xbmc.log('URL TGDIGITAL------: '+str(G.LINK + str(G.PAGENUM)),xbmc.LOGINFO)
        page = urlopen(req)
        html = BeautifulSoup(page, 'html.parser')
        video_tgdigital = html.find('div', class_='article-container').find_all('div', class_='tgla7-news')
        if video_tgdigital:
            get_rows_video_tgdigital(video_tgdigital)
            page = html.find('li', class_='pager-next').find('a')
            pagenext(page)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def video_programma_teche_la7():
    # xbmc.log('LINK------: '+str(G.LINK),xbmc.LOGINFO)
    req = Request(G.LINK + "?page=" + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html.parser')

    if G.PAGENUM == 0:
        # PREVIEW VIDEO
        video_preview = html.find('div', class_='vetrina-protagonista')
        if video_preview:
            get_rows_video_techela7_preview(video_preview)

    # ARCHIVIO VIDEO    
    if html.find('div', class_='view-content clearfix'):
        video_techela7 = html.find('div', class_='view-grouping-content').find_all('div', class_='list-item')
        if video_techela7:
            get_rows_video_techela7(video_techela7)
            page = html.find('li', class_='pager-next')
            pagenext(page)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def first_video(first, titolo, filtro):
    # xbmc.log('FILTRO FIRST: '+ titolo + str(filtro), xbmc.LOGINFO)
    if filtro:
        # xbmc.log('FILTRO TRUE', xbmc.LOGINFO)
        thumblink = first.find('div', class_='holder-bg lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        # xbmc.log('THUMB 1------: '+str(thumb),xbmc.LOGINFO)
        data_orig = first.find('div', class_='scritta_ultima').text.strip()
        data = '[I] - (' + data_orig.replace('/', '.') + ')[/I]'
        try:
            plot = first.find('div', class_='occhiello').text.strip()
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP PLOT1: ' + str(e), xbmc.LOGINFO)
            plot = ""
        link = G.URL_BASE + first.find('a').get('href')
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def video_list(div, titolo, filtro):
    if filtro:
        thumblink = div.find('div', class_='bg-img lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        # xbmc.log('THUMB 2------: '+str(thumb),xbmc.LOGINFO)
        # subdata=div.find('a').get('href')
        # data='[I] - ('+subdata[24:34]+')[/I]'
        try:
            data_orig = div.find('div', class_='data').text.strip()
            data = '[I] - (' + data_orig.replace('/', '.') + ')[/I]'
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('MANCA DATA: ' + str(e), xbmc.LOGINFO)
            data = ""
        plot = ''
        link = G.URL_BASE + div.find('a').get('href')
        # xbmc.log('TEST------: '+str(data),xbmc.LOGINFO)
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def get_rows_video(video):
    for div in video:
        titolo = div.find('div', class_='title').text.strip()
        video_list(div, titolo, True)


def get_rows_video_tgdigital(video):
    for div in video:
        titolo = div.find('h4', class_='news-title').text.strip()
        thumb = div.find('div', class_='news-img').find('a').get('style').split("url(")[1].split(")")[0]
        # Cerca il div della descrizione
        descrizione_div = div.find('div', class_='news-descrizione')
        # Estrai il testo solo se il div esiste, altrimenti usa una stringa vuota
        plot = descrizione_div.text.strip() if descrizione_div else ""
        link = G.URL_BASE_TGDIGITAL + div.find('h4', class_='news-title').find('a').get('href')
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def get_rows_video_techela7_preview(video):
    # xbmc.log('TEST-----: '+str(video),xbmc.LOGINFO)
    regex5 = 'poster: "(.*?)"'
    html = str(video)

    titolo = video.find('a', class_='title').text.strip()
    data = '[I] - (' + video.find('span', class_='date-display-single').text.strip() + ')[/I]'
    # xbmc.log('DATA-----: '+str(data),xbmc.LOGINFO)
    if re.findall(regex5, html):
        # xbmc.log('REGEX----------: '+str(re.findall(regex5, html)),xbmc.LOGINFO)
        thumb = 'https:' + re.findall(regex5, html)[0]
    else:
        thumb = ''
    plot = video.find('div', class_='description').text.strip()
    link = G.URL_BASE + video.find('a', class_='title').get('href')
    liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {'plot': plot})
    add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def get_rows_video_techela7(video):
    for div in video:
        titolo = div.find('div', class_='title').text.strip()
        data = '[I] - (' + div.find('div', class_='data').text.strip() + ')[/I]'
        # xbmc.log('DATA-----: '+str(data),xbmc.LOGINFO)
        thumb = 'https:' + div.find('div', class_='bg-img lozad').get('data-background-image')
        plot = ""
        link = G.URL_BASE + div.a.get('href').strip()
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def get_rows_video_landpage_preview(video):
    #xbmc.log('TEST-----: '+str(video),xbmc.LOGINFO)
    titolo = video.find('div', class_='title_puntata').text.strip()
    data = '[I] - (' + video.find('div', class_='scritta_ultima').text.strip() + ')[/I]'
    thumblink = video.find('div', class_='holder-bg lozad arrow-play').get('data-background-image')
    #thumblink = video.find('div', class_='holder-bg lozad').get('data-background-image')

    plot = ""
    if thumblink.startswith('//'):
        thumb = 'https:' + thumblink
    else:
        thumb = thumblink
    try:
        occhiello = video.find('div', class_='occhiello')
        plot = occhiello.text.strip() if occhiello else ""
    except Exception as e:
        e = sys.exc_info()[0]
        xbmc.log('EXCEP PLOT2: ' + str(e), xbmc.LOGINFO)
        try:
            plot = video.find('div', class_='title_puntata').text.strip()
        except Exception as ee:
            ee = sys.exc_info()[0]
            xbmc.log('EXCEP TITLE_PUNTATA: ' + str(ee), xbmc.LOGINFO)
            plot = ""
    link = G.URL_BASE + video.find('a').get('href')
    liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {'plot': plot})
    add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def get_rows_video_landpage(video):
    # xbmc.log('VIDEO-----: '+str(video),xbmc.LOGINFO)
    for div in video:
        titolo = div.find('div', class_='occhiello').text.strip()
        # xbmc.log('TITOLO-----: '+str(titolo),xbmc.LOGINFO)
        data = '[I] - (' + div.find('div', class_='data').text.strip() + ')[/I]'
        thumblink = div.find('div', class_='bg-img lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        plot = ""
        link = G.URL_BASE + div.a.get('href').strip()
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def pagenext(pagenb):
    if pagenb:
        liStyle = xbmcgui.ListItem('[B]' + G.LANGUAGE(32003) + '[/B]', offscreen=True)
        liStyle.setArt({'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "link": G.LINK, "page": G.PAGENUM + 1}, liStyle)


def run(argv):
    """ Addon entry point """
    G.init_globals(argv)

    if G.PARAMS.get("page", "") == "":
        G.PAGENUM = 0
    else:
        G.PAGENUM = int(G.PARAMS.get("page", ""))

    try:
        dispatch()
    except Exception as exc:
        # A page that changed or a network error must never escape as a Python
        # traceback: Kodi would only report "GetDirectory ... failed"
        xbmc.log('RivediLA7: %s raised %s: %s' % (G.MODE, type(exc).__name__, exc), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)


def dispatch():
    """ Route the request to the function of the current mode """
    if G.MODE == "diretta_la7":
        play_dirette(G.URL_LIVE_LA7, True)

    elif G.MODE == "diretta_la7cinema":
        play_dirette(G.URL_LIVE_LA7CINEMA, True)

    elif G.MODE == "diretta_la7eventi":
        play_dirette(G.URL_LIVE_LA7EVENTI, True)

    elif G.MODE == "rivedi_la7":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7, 'rivedila7.jpg')
            else:
                rivedi_giorno()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "rivedi_la7cinema":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7CINEMA, 'direttalivela7cinema.jpg')
            else:
                rivedi_giorno()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "tg_meteo":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera_tg_meteo()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "tutti_programmi":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "la7_prime":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_la7prime()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "teche_la7":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera_teche_la7()
            else:
                mostra_biografia()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "documentari":
        if G.PLAY == "":
            documentari()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "cerca_la7":
        if G.PLAY == "":
            cerca_la7()
        else:
            xbmcgui.Window(10000).setProperty('la7_video_in_corso', '1')
            play_video(G.PLAY, False)

    else:
        show_root_menu()
