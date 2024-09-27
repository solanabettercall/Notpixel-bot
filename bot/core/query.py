import asyncio
import random
from time import time

import aiohttp
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from bot.core.agents import generate_random_user_agent
from bot.config import settings
import cloudscraper

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from random import randint

import urllib3
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class Tapper:
    def __init__(self, query: str, session_name):
        self.query = query
        self.session_name = session_name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.last_claim = None
        self.last_checkin = None
        self.balace = 0
        self.maxtime = 0
        self.fromstart = 0
        self.checked = [False] * 5

    # async def get_tg_web_data(self, proxy: str | None) -> str:
    #     try:
    #         if settings.REF_LINK == "":
    #             ref_param = "f6624523270"
    #         else:
    #             ref_param = settings.REF_LINK.split("=")[1]
    #     except:
    #         logger.error(f"{self.session_name} | Ref link invaild please check again !")
    #         sys.exit()
    #     if proxy:
    #         proxy = Proxy.from_str(proxy)
    #         proxy_dict = dict(
    #             scheme=proxy.protocol,
    #             hostname=proxy.host,
    #             port=proxy.port,
    #             username=proxy.login,
    #             password=proxy.password
    #         )
    #     else:
    #         proxy_dict = None
    #
    #     self.tg_client.proxy = proxy_dict
    #
    #     try:
    #         if not self.tg_client.is_connected:
    #             try:
    #                 await self.tg_client.connect()
    #             except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
    #                 raise InvalidSession(self.session_name)
    #
    #         while True:
    #             try:
    #                 peer = await self.tg_client.resolve_peer('notpixel')
    #                 break
    #             except FloodWait as fl:
    #                 fls = fl.value
    #
    #                 logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
    #                 logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")
    #
    #                 await asyncio.sleep(fls + 3)
    #
    #         web_view = await self.tg_client.invoke(RequestAppWebView(
    #             peer=peer,
    #             app=InputBotAppShortName(bot_id=peer, short_name="app"),
    #             platform='android',
    #             write_allowed=True,
    #             start_param=ref_param
    #         ))
    #
    #         auth_url = web_view.url
    #         # print(auth_url)
    #         tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
    #         # print(tg_web_data)
    #
    #         if self.tg_client.is_connected:
    #             await self.tg_client.disconnect()
    #
    #         return tg_web_data
    #
    #     except InvalidSession as error:
    #         raise error
    #
    #     except Exception as error:
    #         logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
    #                      f"{error}")
    #         await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy):
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")
            return False

    def login(self, session: cloudscraper.CloudScraper):
        response = session.get("https://notpx.app/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            logger.success(f"{self.session_name} | <green>Logged in.</green>")
            return True
        else:
            print(response.json())
            logger.warning("{self.session_name} | <red>Failed to login</red>")
            return False

    def get_user_data(self, session: cloudscraper.CloudScraper):
        response = session.get("https://notpx.app/api/v1/mining/status", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(response.json())
            return None

    def generate_random_color(self):
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
        return "#{:02X}{:02X}{:02X}".format(r, g, b)

    def generate_random_pos(self):
        return randint(1, 1000000)

    def repaint(self, session: cloudscraper.CloudScraper, chance_left):
        payload = {
            "newColor": str(self.generate_random_color()),
            "pixelId": int(self.generate_random_pos())
        }
        response = session.post("https://notpx.app/api/v1/repaint/start", headers=headers, json=payload)
        if response.status_code == 200:
            logger.success(
                f"{self.session_name} | <green>Repaint successfully balace: <light-blue>{response.json()['balance']}</light-blue> | Repaint left: <yellow>{chance_left}</yellow></green>")
        else:
            logger.warning(f"{self.session_name} | Faled to repaint: {response.json()}")

    def auto_task(self, session: cloudscraper.CloudScraper):
        pass

    async def auto_upgrade(self, session: cloudscraper.CloudScraper):
        res = session.get("https://notpx.app/api/v1/mining/boost/check/paintReward", headers=headers)
        if res.status_code == 200:
            logger.success(f"{self.session_name} | <green>Upgrade paint reward successfully!</green>")
        await asyncio.sleep(random.uniform(2, 4))
        res = session.get("https://notpx.app/api/v1/mining/boost/check/reChargeSpeed", headers=headers)
        if res.status_code == 200:
            logger.success(f"{self.session_name} | <green>Upgrade recharging speed successfully!</green>")
        await asyncio.sleep(random.uniform(2, 4))
        res = session.get("https://notpx.app/api/v1/mining/boost/check/energyLimit", headers=headers)
        if res.status_code == 200:
            logger.success(f"{self.session_name} | <green>Upgrade energy limit successfully!</green>")

    def claimpx(self, session: cloudscraper.CloudScraper):
        res = session.get("https://notpx.app/api/v1/mining/claim", headers=headers)
        if res.status_code == 200:
            logger.success(
                f"{self.session_name} | <green>Successfully claimed <cyan>{res.json()['claimed']} px</cyan> from mining!</green>")
        else:
            logger.warning(f"{self.session_name} | <yellow>Failed to claim px from mining: {res.json()}</yellow>")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = generate_random_user_agent(device_type='android', browser_type='chrome')
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)
        session = cloudscraper.create_scraper()
        session.mount('https://', SSLAdapter())

        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                proxy_type = proxy.split(':')[0]
                proxies = {
                    proxy_type: proxy
                }
                session.proxies.update(proxies)
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")

        token_live_time = randint(3500, 3600)
        while True:
            try:
                if time() - access_token_created_time >= token_live_time:
                    # tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    headers['Authorization'] = f"initData {self.query}"
                    access_token_created_time = time()
                    token_live_time = randint(3500, 3600)

                if self.login(session):
                    user = self.get_user_data(session)

                    if user:
                        self.maxtime = user['maxMiningTime']
                        self.fromstart = user['fromStart']
                        logger.info(
                            f"{self.session_name} | Pixel Balance: <light-blue>{int(user['userBalance'])}</light-blue> | Pixel available to paint: <cyan>{user['charges']}</cyan>")

                        if self.fromstart >= self.maxtime / 2:
                            self.claimpx(session)
                            await asyncio.sleep(random.uniform(2, 5))
                        if settings.AUTO_TASK:
                            res = session.get("https://notpx.app/api/v1/mining/task/check/x?name=notpixel",
                                              headers=headers)
                            if res.status_code == 200 and res.json()['x:notpixel'] and self.checked[1] is False:
                                self.checked[1] = True
                                logger.success("<green>Task Not pixel on x completed!</green>")
                            res = session.get("https://notpx.app/api/v1/mining/task/check/x?name=notcoin",
                                              headers=headers)
                            if res.status_code == 200 and res.json()['x:notcoin'] and self.checked[2] is False:
                                self.checked[2] = True
                                logger.success("<green>Task Not coin on x completed!</green>")
                            res = session.get("https://notpx.app/api/v1/mining/task/check/paint20pixels",
                                              headers=headers)
                            if res.status_code == 200 and res.json()['paint20pixels'] and self.checked[3] is False:
                                self.checked[3] = True
                                logger.success("<green>Task paint 20 pixels completed!</green>")
                        if user['charges'] > 0:
                            total_chance = int(user['charges'])
                            while total_chance > 0:
                                total_chance -= 1
                                self.repaint(session, total_chance)
                                sleep_ = random.uniform(2, 5)
                                logger.info(f"{self.session_name} | Sleep <cyan>{sleep_}</cyan> before continue...")

                        if settings.AUTO_UPGRADE:
                            await self.auto_upgrade(session)

                    else:
                        logger.warning(f"{self.session_name} | <yellow>Failed to get user data!</yellow>")

                sleep_ = randint(500, 1000)
                logger.info(f"{self.session_name} | Sleep {sleep_}s...")
                await asyncio.sleep(sleep_)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))


async def run_query_tapper(query: str, name: str, proxy: str | None):
    try:
        sleep_ = randint(1, 15)
        logger.info(f" start after {sleep_}s")
        # await asyncio.sleep(sleep_)
        await Tapper(query=query, session_name=name).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"Invalid Query: {query}")