#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author:  Sg4Dylan -- <sg4dylan#gmail.com>
# Licence: GPLv3
import argparse
import os
import requests
import re
import json
import time
import logging

REGX_XUNLEI = re.compile('''
^(?:
    7\.|sd|xl|-XL|xun|
    unknown\s(?:
        bt/7\.(?!
            (?:9|10)\.\d\D  | # BitTorrent
            0\.0\.0$          # BitTorrent?
        )|
        sd|xl
    )
)
''', re.I | re.X)
REGX_PLAYER = re.compile('''
^(?:
    dan               | # DanDan (DL)
    stellarplayer     | # SP
    DLB|dlb           | # DLBT (DL)
    [Qq]vo            | # Qvod (QVOD) [Dead]
    [Ss]od            | # Soda
    [Tt]orc           | # Torch (TB)
    [Vv]ag            | # Vagaa (VG) [Dead?]
    [Xx]fp            | # Xfplay (XF)
    [Sp]sp            | # SP
    Unknown\s(?:
        DL            | # DanDan/DLBT (DL)
        QVO           | # Qvod (QVOD) [Dead]
        TB            | # Torch (TB)
        UW            | # uTorrent Web (UW)
        VG            | # Vagaa (VG) [Dead?]
        XF            | # Xfplay (XF)
        SP              # SP
    )
)
''', re.X)
REGX_OTHERS = re.compile('''
^(?:
    caca              | # Cacaoweb
    [Ff]lash[Gg]      | # FlashGet (FG)
    .+?ransp          | # Net Transport (NX) - need more infomation
    [Qq]{2}           | # QQ (QD) [Dead?]
    [Tt]uo            | # TuoTu (TT) [Dead?]
    Unknown\s(?:
        BN            | # Baidu (BN) [Dead?]
        FG            | # FlashGet (FG)
        NX            | # Net Transport (NX)
        QD            | # QQ (QD) [Dead?]
        TT              # TuoTu (TT) [Dead?]
    )
)
''', re.X)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class VampireHunter:
    SESSION = requests.Session()
    # WebUI 地址
    API_PREFIX = os.getenv('API_PREFIX', 'http://127.0.0.1:8080')
    API_FULL = f'{API_PREFIX}/api/v2'
    # WebUI 用户名密码
    API_USERNAME = os.getenv('API_USERNAME', '')
    API_PASSWORD = os.getenv('API_PASSWORD', '')
    # 如果你套了 nginx 做额外的 basicauth
    BASICAUTH_ENABLED = str2bool(os.getenv('BASICAUTH_ENABLED', 'false'))
    BASICAUTH_USERNAME = os.getenv('BASICAUTH_USERNAME', '')
    BASICAUTH_PASSWORD = os.getenv('BASICAUTH_PASSWORD', '')
    # 检测间隔
    INTERVAL_SECONDS = int(os.getenv('INTERVAL_SECONDS', 5))
    # 屏蔽时间
    DEFAULT_BAN_SECONDS = int(os.getenv('DEFAULT_BAN_SECONDS', 3600))
    # 屏蔽开关
    BAN_XUNLEI = str2bool(os.getenv('BAN_XUNLEI', 'true'))
    BAN_PLAYER = str2bool(os.getenv('BAN_PLAYER', 'true'))
    BAN_OTHERS = str2bool(os.getenv('BAN_OTHERS', 'false'))
    # 识别到客户端直接屏蔽不管是否存在上传
    BAN_WITHOUT_RATIO_CHECK = str2bool(os.getenv('BAN_WITHOUT_RATIO_CHECK', 'true'))

    __banned_ips = {}
    logging.basicConfig(level=logging.INFO)

    def execute_login(self):
        return self.SESSION.post(
            f'{self.API_FULL}/auth/login',
            data={
                'username': self.API_USERNAME,
                'password': self.API_PASSWORD
            }
        ).text;

    def __init__(self):
        self.login_status = self.execute_login()
        logging.warning(f'Login status: {self.login_status}')

    def get_basicauth(self):
        if self.BASICAUTH_ENABLED:
            return (self.BASICAUTH_USERNAME, self.BASICAUTH_PASSWORD)
        else:
            return None

    def get_torrents(self):
        return self.SESSION.get(
            f'{self.API_FULL}/torrents/info',
            auth=self.get_basicauth()
        ).json()

    def get_peers(self, mission_hash):
        return self.SESSION.get(
            f'{self.API_FULL}/sync/torrentPeers?hash={mission_hash}',
            auth=self.get_basicauth()
        ).json()

    def sumbit_banned_ips(self):
        ips = ''
        now = time.time()
        tmp_banned_ips = self.__banned_ips.copy()
        for key, value in tmp_banned_ips.items():
            if now > value['expired']:
                del self.__banned_ips[key]
                continue
            ip = key.strip('[]')  # 去除IPV6地址字符串中的大括号
            ips += ip + '\n'
        self.SESSION.post(
            f'{self.API_FULL}/app/setPreferences',
            auth=self.get_basicauth(),
            data={
                'json': json.dumps({
                    'banned_IPs': ips
                })
            }
        )

    def do_once_banip(self):

        def parse_ip(ip_port):
            port_path = ip_port.rfind(':')
            ip = ''
            if ip_port.startswith('::ffff:'):
                ip = ip_port[7:port_path]
            else:
                ip = ip_port[:port_path]
            return ip

        def check_peer(info):
            target_client = False
            # 屏蔽迅雷
            if self.BAN_XUNLEI and REGX_XUNLEI.search(info['client']):
                target_client = True
            # 屏蔽 P2P 播放器
            if self.BAN_PLAYER and REGX_PLAYER.search(info['client']):
                target_client = True
            # 屏蔽野鸡客户端
            if self.BAN_OTHERS and REGX_OTHERS.search(info['client']):
                target_client = True
            # 不检查分享率及下载进度直接屏蔽
            if self.BAN_WITHOUT_RATIO_CHECK:
                return target_client
            # 分享率及下载进度异常
            if not target_client:
                return False
            logging.info(f'Detected target client: {info["client"]}')
            if info['progress'] == 0 and info['uploaded'] > 1000000:
                return True

        def filter_ip(peers, now):
            for ip_port, info in peers['peers'].items():
                if check_peer(info):
                    ip = parse_ip(ip_port)
                    logging.warning(f'Banned: {ip}, UA: {info["client"]}')
                    self.__banned_ips[ip] = {
                        'ban_time': now,
                        'expired': now + self.DEFAULT_BAN_SECONDS
                    }

        torrents = self.get_torrents()
        now = time.time()
        logging.info(f'Now: {now} All torrents: {len(torrents)}')
        for torrent in torrents:
            peers = self.get_peers(torrent['hash'])
            # logging.info(f'Peers: {len(peers)}\tTorrent: {torrent["name"]}')
            filter_ip(peers, now)
        self.sumbit_banned_ips()

    def start(self):
        if 'Fails' in self.login_status:
            logging.warning('Please check login credentials.')
            return
        while True:
            try:
                self.do_once_banip()
            except:
                try:
                    self.execute_login() # Re-login, script may stop working after long time execute
                except:
                    logging.info(f'An error throwing, is WebUI request timed out?')
            finally:
                time.sleep(self.INTERVAL_SECONDS)


if __name__ == '__main__':
    hunter = VampireHunter()
    hunter.start()
