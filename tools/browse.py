#!/usr/bin/env python3
"""Walk the add-on sections from a shell, without Kodi.

The module imports xbmc/xbmcgui/xbmcplugin from this file before loading the
add-on, so browsing can be exercised and diffed while iterating on the
scrapers.

    tools/browse.py --modes                     list the add-on modes
    tools/browse.py rivedi_la7                  list a section
    tools/browse.py rivedi_la7 giorno=31-10-2026
    tools/browse.py --depth 2 programmi         follow folder items too
    tools/browse.py --url https://www.la7play.it/film
                                                list the nodes of any page
    tools/browse.py --play https://www.la7play.it/film/il-negoziatore-396455
                                                show what playback would open
"""
import argparse
import datetime
import json
import os
import sys
import types
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

ITEMS = []
RESOLVED = []
DIALOGS = []


def install_stubs():
    """Minimal xbmc* objects, enough for the browsing code paths."""
    xbmc = types.ModuleType('xbmc')
    xbmc.LOGDEBUG, xbmc.LOGINFO, xbmc.LOGWARNING, xbmc.LOGERROR = 0, 1, 2, 3
    xbmc.log = lambda msg, level=xbmc.LOGINFO: print('[kodi %d] %s' % (level, msg))

    class Window:
        def __init__(self, wid=0):
            self.props = {}

        def setProperty(self, key, value):
            self.props[key] = value

        def getProperty(self, key):
            return self.props.get(key, '')

        def clearProperty(self, key):
            self.props.pop(key, None)

    xbmc.Window = Window

    xbmcgui = types.ModuleType('xbmcgui')

    class ListItem:
        def __init__(self, label='', offscreen=False):
            self.label, self.art, self.info, self.props, self.path = label, {}, {}, {}, ''

        def setArt(self, art):
            self.art.update(art)

        def setInfo(self, kind, info):
            self.info.setdefault(kind, {}).update(info)

        def setProperty(self, key, value):
            self.props[key] = value

        def setPath(self, path):
            self.path = path

        def setMimeType(self, mime):
            pass

        def setContentLookup(self, value):
            pass

    class Dialog:
        def ok(self, heading, message):
            DIALOGS.append((heading, message))
            print('[dialog] %s / %s' % (heading, message))

        def notification(self, heading, message, icon=None, time=5000):
            print('[notification] %s / %s' % (heading, message))

    xbmcgui.ListItem, xbmcgui.Dialog, xbmcgui.Window = ListItem, Dialog, Window

    xbmcplugin = types.ModuleType('xbmcplugin')
    xbmcplugin.addDirectoryItem = lambda handle, url, listitem, isFolder=True: ITEMS.append(
        {'url': url, 'label': listitem.label, 'item': listitem, 'folder': isFolder}) or True
    xbmcplugin.endOfDirectory = lambda handle, succeeded=True, **kw: ITEMS.append(
        {'end': True, 'succeeded': succeeded})
    xbmcplugin.setResolvedUrl = lambda handle, succeeded, listitem: RESOLVED.append(
        {'succeeded': succeeded, 'item': listitem})
    xbmcplugin.setContent = lambda handle, content: None
    xbmcplugin.addSortMethod = lambda handle, method: None
    for name in ('SORT_METHOD_LABEL', 'SORT_METHOD_LABEL_IGNORE_FOLDERS', 'SORT_METHOD_NONE',
                 'SORT_METHOD_UNSORTED', 'SORT_METHOD_TITLE', 'SORT_METHOD_VIDEO_TITLE',
                 'SORT_METHOD_DATE', 'SORT_METHOD_EPISODE'):
        setattr(xbmcplugin, name, 0)

    xbmcaddon = types.ModuleType('xbmcaddon')

    class Addon:
        def getAddonInfo(self, key):
            return {'path': REPO, 'profile': '/tmp/kodi_profile', 'id': 'plugin.video.rivedila7',
                    'name': 'LA7-LA7Cinema', 'icon': os.path.join(REPO, 'resources', 'icon.png')}.get(key, '')

        def getLocalizedString(self, sid):
            return 'string %d' % sid

        def getSetting(self, key):
            return ''

    xbmcaddon.Addon = Addon

    helper = types.ModuleType('inputstreamhelper')

    class Helper:
        def __init__(self, protocol, drm=None):
            self.inputstream_addon = 'inputstream.adaptive'

        def check_inputstream(self):
            return True

    helper.Helper = Helper

    requests = types.ModuleType('requests')

    class Response:
        def __init__(self, body):
            self.body = body
            self.content = body.encode()

        def json(self):
            return __import__('json').loads(self.body)

        def decode(self, *a, **kw):
            return self.body

    def get(url, headers=None, verify=True, **kw):
        req = urllib.request.Request(url, headers={'user-agent': 'Mozilla/5.0', **(headers or {})})
        with urllib.request.urlopen(req, timeout=40) as resp:
            return Response(resp.read().decode('utf-8', 'replace'))

    requests.get = get

    bs4 = types.ModuleType('bs4')

    class BeautifulSoup:
        def __init__(self, page, parser='html.parser'):
            raise RuntimeError('bs4 is not available: the legacy scraper was called')

    bs4.BeautifulSoup = BeautifulSoup

    for name, module in (('xbmc', xbmc), ('xbmcgui', xbmcgui), ('xbmcplugin', xbmcplugin),
                         ('xbmcaddon', xbmcaddon), ('inputstreamhelper', helper),
                         ('requests', requests), ('bs4', bs4)):
        sys.modules.setdefault(name, module)


def run_addon(query):
    """Invoke the add-on entry point and return (items, resolved, dialogs)."""
    install_stubs()
    ITEMS.clear()
    RESOLVED.clear()
    DIALOGS.clear()
    from resources.lib import plugin
    plugin.run(['plugin://plugin.video.rivedila7/', '1', query])
    return [i for i in ITEMS if not i.get('end')], list(RESOLVED), list(DIALOGS)


def mode_url(mode, params):
    return '?' + urllib.parse.urlencode({'mode': mode, **params})


def walk(mode, params, depth, indent=0):
    items, _, dialogs = run_addon(mode_url(mode, params))
    for item in items:
        print('%s%s  %s' % ('  ' * indent, item['label'], item['url'].split('?', 1)[-1][:100]))
    if not items:
        print('%s(no entries)' % ('  ' * indent))
    if depth > 1:
        for item in items:
            if not item['folder']:
                continue
            query = urllib.parse.urlsplit(item['url']).query
            child = dict(urllib.parse.parse_qsl(query))
            child_mode = child.pop('mode', mode)
            walk(child_mode, child, depth - 1, indent + 1)
    return items, dialogs


def smoke():
    """ Walk every section and report the ones that no longer list anything """
    today = datetime.date.today().strftime('%d-%m-%Y')
    sections = [
        ('rivedi_la7', {}, 3),
        ('rivedi_la7cinema', {}, 1),
        ('rivedi_la7', {'giorno': today}, 3),
        ('la7_prime', {}, 1),
        ('la7_prime', {'link': 'https://www.la7play.it/film'}, 10),
        ('tutti_programmi', {}, 20),
    ]
    failures = 0
    for mode, params, minimum in sections:
        items, _, dialogs = run_addon(mode_url(mode, params))
        ok = len(items) >= minimum and not dialogs
        failures += 0 if ok else 1
        print('%-4s %-18s %-46s %3d entries (min %d) %d dialogs' % (
            'ok' if ok else 'FAIL', mode, str(params), len(items), minimum, len(dialogs)))
    print('%d section(s) failing' % failures)
    return 0 if not failures else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('mode', nargs='?', help='add-on mode, e.g. rivedi_la7')
    parser.add_argument('params', nargs='*', help='extra query parameters, key=value')
    parser.add_argument('--modes', action='store_true', help='list the known modes')
    parser.add_argument('--depth', type=int, default=1, help='follow folder items (default 1)')
    parser.add_argument('--url', help='list the content nodes of a la7play.it page')
    parser.add_argument('--play', help='resolve the stream of a la7play.it page')
    parser.add_argument('--gql', metavar='NAME', help='run a la7play.it query, key=value variables')
    parser.add_argument('--smoke', action='store_true', help='walk every section, fail if one is empty')
    args = parser.parse_args()

    install_stubs()

    if args.modes:
        for mode in ('rivedi_la7', 'rivedi_la7cinema', 'diretta_la7', 'diretta_la7cinema',
                     'diretta_la7eventi', 'tg_meteo', 'programmi', 'teche_la7', 'la7_prime',
                     'cerca_la7'):
            print(mode)
        return 0

    from resources.lib import plugin

    if args.url:
        for node in plugin.la7play_nodes(args.url):
            print('%-46s %s' % ((node.get('path') or node.get('pathname'))[:46],
                                node.get('titolo') or node.get('title') or node.get('nome')))
        return 0

    if args.gql:
        variables = {key: value for key, value in (arg.split('=', 1) for arg in args.params)} or None
        print(json.dumps(plugin.gql(args.gql, variables), indent=2, ensure_ascii=False)[:4000])
        return 0

    if args.smoke:
        return smoke()

    if args.play:
        _, resolved, dialogs = run_addon(mode_url('rivedi_la7', {'play': args.play, 'titolo': 't'}))
        for entry in resolved:
            item = entry['item']
            print('resolved=%s' % entry['succeeded'])
            print('path=%s' % item.path)
            for key, value in sorted(item.props.items()):
                print('%s=%s' % (key, value))
        if not resolved:
            print('(nothing resolved)')
        return 0

    if not args.mode:
        parser.print_help()
        return 1

    params = dict(arg.split('=', 1) for arg in args.params)
    items, dialogs = walk(args.mode, params, args.depth)
    print('-- %d entries, %d dialogs' % (len(items), len(dialogs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
