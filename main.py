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
import pytz
import logging
import urllib3
import validators
from itertools import chain
from datetime import datetime

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
    # WebUI 地址
    API_BASE_ENDPOINT = f"{os.getenv('API_PREFIX', 'http://localhost:8080')}/api/v2"
    # 是否验证Https证书有效性，如果你使用HTTPS自签名证书或通过局域网IP而非证书相关联的域名访问，请关闭此选项
    API_VERIFY_HTTPS_CERT = str2bool(os.getenv('API_VERIFY_HTTPS_CERT', 'true'))
    # WebUI 用户名密码
    API_USERNAME = os.getenv('API_USERNAME', '')
    API_PASSWORD = os.getenv('API_PASSWORD', '')
    # 如果你套了 nginx 做额外的 basicauth
    BASICAUTH_ENABLED = str2bool(os.getenv('BASICAUTH_ENABLED', 'false'))
    BASICAUTH_USERNAME = os.getenv('BASICAUTH_USERNAME', '')
    BASICAUTH_PASSWORD = os.getenv('BASICAUTH_PASSWORD', '')
    # 检测间隔
    INTERVAL_SECONDS = int(os.getenv('INTERVAL_SECONDS', 5))
    # 默认时区
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'Asia/Shanghai')
    # 日志级别
    DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    # 屏蔽时间
    DEFAULT_BAN_SECONDS = int(os.getenv('DEFAULT_BAN_SECONDS', 3600))
    # 屏蔽开关
    BAN_XUNLEI = str2bool(os.getenv('BAN_XUNLEI', 'true'))
    BAN_PLAYER = str2bool(os.getenv('BAN_PLAYER', 'true'))
    BAN_OTHERS = str2bool(os.getenv('BAN_OTHERS', 'false'))
    # 识别到客户端直接屏蔽不管是否存在上传
    BAN_WITHOUT_RATIO_CHECK = str2bool(os.getenv('BAN_WITHOUT_RATIO_CHECK', 'true'))

    BANNED_IPS_LIST = {}

    SESSION = requests.Session()
    SESSION.verify = API_VERIFY_HTTPS_CERT

    # 禁用 HTTPS 证书验证警告
    if not API_VERIFY_HTTPS_CERT:
        urllib3.disable_warnings()
        logging.debug('HTTPS certificate verification warnings has been disabled')
    
    def __init__(self):
        if self.DEFAULT_TIMEZONE not in pytz.all_timezones:
            raise argparse.ArgumentError(self.DEFAULT_TIMEZONE, 'Invalid timezone')
        
        if self.DEFAULT_LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise argparse.ArgumentError(self.DEFAULT_LOG_LEVEL, 'Invalid log level')
        
        if not validators.url(self.API_BASE_ENDPOINT):
            raise argparse.ArgumentError(self.API_BASE_ENDPOINT, 'Invalid API base endpoint')

        logging.basicConfig(level=self.DEFAULT_LOG_LEVEL)

    def request_login(self):
        loginAPIEndpoint = f'{self.API_BASE_ENDPOINT}/auth/login'

        logging.debug(f"POST to API Endpoint: '{loginAPIEndpoint}'")

        login_response = self.SESSION.post(
            loginAPIEndpoint,
            data={
                'username': self.API_USERNAME,
                'password': self.API_PASSWORD
            }
        )

        logging.info(f'Login status: {login_response.text}')
        logging.debug(f"Login API Response - statusCode: {login_response.status_code}, body: '{login_response.text}'")

        return 'Ok' in login_response.text

    def get_basicauth(self):
        if self.BASICAUTH_ENABLED:
            return (self.BASICAUTH_USERNAME, self.BASICAUTH_PASSWORD)
        else:
            return None

    def get_torrents(self):
        torrentsAPIEndpoint = f'{self.API_BASE_ENDPOINT}/torrents/info'

        logging.debug(f"GET to API Endpoint: '{torrentsAPIEndpoint}'")

        torrents_Response = self.SESSION.get(
            torrentsAPIEndpoint,
            auth=self.get_basicauth()
        )

        logging.debug(f"Torrents API Response - statusCode: {torrents_Response.status_code}, body: '{torrents_Response.text}'")

        return torrents_Response.json()

    def get_peers(self, torrentHash):
        peersAPIEndpoint = f'{self.API_BASE_ENDPOINT}/sync/torrentPeers?hash={torrentHash}'

        logging.debug(f"GET to API Endpoint: '{peersAPIEndpoint}'")

        peers_Response = self.SESSION.get(
            peersAPIEndpoint,
            auth=self.get_basicauth()
        )

        logging.debug(f"Peers API Response - statusCode: {peers_Response.status_code}, body: '{peers_Response.text}'")

        return peers_Response.json()
    
    def convert_size(self, value):
        size = 1024.0
        units = ["B", "KB", "MB", "GB", "TB"]
        
        for index in range(len(units)):
            if (value / size) < 1:
                return "%.2f%s" % (value, units[index])
            value = value / size

        return 'Unknown'

    def submit_banned_ips(self, new_banned_ips):
        now = time.time()

        logging.debug(f"Current BANNED_IPS_LIST: {self.BANNED_IPS_LIST}")
        logging.debug(f'Current Ban Seconds: {self.DEFAULT_BAN_SECONDS}')

        # 添加需要屏蔽的 IP 列表
        for ip, value in map(lambda ip: (ip, { 'ban_time': now, 'expired_on': now + self.DEFAULT_BAN_SECONDS }), new_banned_ips):
            if ip not in self.BANNED_IPS_LIST:
                self.BANNED_IPS_LIST[ip] = value
                logging.debug(f'IP: {ip} has been added to banned list')
        
        # 清除超过封锁期限的 IP 列表
        for ip in filter(lambda ip: now >= self.BANNED_IPS_LIST[ip]['expired_on'], self.BANNED_IPS_LIST.keys()):
            if ip in self.BANNED_IPS_LIST:
                self.BANNED_IPS_LIST.pop(ip)
                logging.debug(f'IP: {ip} has been removed from banned list')

        logging.debug(f"Banned IPs Submitted: [{', '.join(map(lambda ip: ip.strip('[]'), self.BANNED_IPS_LIST.keys()))}]")

        self.SESSION.post(
            f'{self.API_BASE_ENDPOINT}/app/setPreferences',
            auth=self.get_basicauth(),
            data={
                'json': json.dumps({
                    'banned_IPs': '\n'.join(map(lambda ip: ip.strip('[]'), self.BANNED_IPS_LIST.keys()))
                })
            }
        )

    def check_peer(self, info):
        target_client = False

        logging.debug(f'Xunlei Ban Enabled: {self.BAN_XUNLEI}')
        logging.debug(f'Player Ban Enabled: {self.BAN_PLAYER}')
        logging.debug(f'Others Ban Enabled: {self.BAN_OTHERS}')

        # 屏蔽迅雷
        if self.BAN_XUNLEI and REGX_XUNLEI.search(info['client']):
            target_client = True
            logging.debug(f'Xunlei Peer Detected - IP: {info["ip"]}, UA: {info["client"]}')
        # 屏蔽 P2P 播放器
        elif self.BAN_PLAYER and REGX_PLAYER.search(info['client']):
            target_client = True
            logging.debug(f'Player Peer Detected - IP: {info["ip"]}, UA: {info["client"]}')
        # 屏蔽野鸡客户端
        elif self.BAN_OTHERS and REGX_OTHERS.search(info['client']):
            target_client = True
            logging.debug(f'Other Peer Detected - IP: {info["ip"]}, UA: {info["client"]}')

        logging.debug(f'Ban Without Ratio Check: {self.BAN_WITHOUT_RATIO_CHECK}')
        
        # 不检查分享率及下载进度直接屏蔽
        if self.BAN_WITHOUT_RATIO_CHECK:
            if target_client:
                logging.warning(f"Peer Banned - IP: {info['ip']}, UA: {info['client']}, Country: {info['country']}")
                return True
        elif target_client:
            logging.debug(f"Ratio Check Peer - IP: {info['ip']}, UA: {info['client']}")
            logging.debug(f"Ratio Check Peer Information - Progress: {'%.1f%%' % (info['progress'] * 100)}, Downloaded: {self.convert_size(info['downloaded'])}, Uploaded: {self.convert_size(info['uploaded'])}")

            # 分享率为0且下载量为0且上传量大于1MB，确定此客户端为吸血BT客户端，予以屏蔽
            if info['progress'] == 0 and info['downloaded'] == 0 and info['uploaded'] > 1048576:
                logging.warning(f"Peer Banned - IP: {info['ip']}, UA: {info['client']}, Country: {info['country']}")
                return True

        logging.debug(f"Peer Allowed - IP: {info['ip']}, UA: {info['client']}, Country: {info['country']}")

        return False

    def filter_torrent(self, torrent):
        torrentPeers = self.get_peers(torrent['hash'])
        torrentPeersInfo = torrentPeers['peers'].values()

        logging.debug(f"Torrent: {torrent['name']}, Peers: {len(torrentPeersInfo)}, Hash: {torrent['hash']}")

        return list(map(lambda info: info['ip'], filter(lambda info: self.check_peer(info), torrentPeersInfo)))

    def collect_and_ban_ip(self):        
        torrents = self.get_torrents()
        nowDescription = datetime.now(pytz.timezone(self.DEFAULT_TIMEZONE)).strftime('%Y-%m-%dT%H:%M:%S%z')

        logging.debug(f'Current Timezone: {self.DEFAULT_TIMEZONE}')
        logging.info(f'Current Date: {nowDescription}, torrents found: {len(torrents)}')

        self.submit_banned_ips(set(chain.from_iterable(map(lambda torrent: self.filter_torrent(torrent), torrents))))

    def start(self):
        try:
            login_status = self.request_login()
        except Exception as loginException:
            login_status = False
            logging.error(f'Unexpected exception was throw during attempting login: {repr(loginException)}')

        while login_status:
            try:
                self.collect_and_ban_ip()
            except Exception as banIPException:
                logging.error(f'Unexpected exception was throw during attempting ban IP: {repr(banIPException)}')

                # Re-login, script may stop working after long time execute
                try:
                    login_status = self.request_login()
                except Exception as reLoginException:
                    login_status = False
                    logging.error(f'Unexpected exception was throw during attempting re-login: {repr(reLoginException)}')

                continue

            logging.debug(f'Waiting for {self.INTERVAL_SECONDS} seconds...')

            time.sleep(self.INTERVAL_SECONDS)

        logging.critical('Unable retrieve the authorization from API. Please check login credentials or any configuration issues.')



if __name__ == '__main__':
    hunter = VampireHunter()
    hunter.start()
