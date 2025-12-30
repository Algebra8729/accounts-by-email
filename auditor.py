import asyncio
import httpx
import random
import string
import json
import sys
import time
import re
from datetime import datetime
from argparse import ArgumentParser

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class ZeroTraceAuditor:
    def __init__(self, email, timeout=12):
        self.email = email
        self.timeout = timeout
        self.results = []
        self.start_time = time.time()
        self.client = httpx.AsyncClient(timeout=self.timeout, http2=True, follow_redirects=True)

    def get_headers(self, custom=None):
        h = {"User-Agent": random.choice(UA_LIST), "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
        if custom: h.update(custom)
        return h

    async def check_instagram(self):
        try:
            r = await self.client.get("https://www.instagram.com/accounts/emailsignup/", headers=self.get_headers())
            token = r.text.split('{"config":{"csrf_token":"')[1].split('"')[0]
            h = self.get_headers({"x-csrftoken": token, "Referer": "https://www.instagram.com/"})
            d = {"email": self.email, "username": "".join(random.choices(string.ascii_lowercase, k=12)), "first_name": "Audit"}
            res = await self.client.post("https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/", data=d, headers=h)
            self.results.append({"s": "Instagram", "e": "email_is_taken" in res.text or "email_sharing_limit" in res.text})
        except: self.results.append({"s": "Instagram", "e": False, "err": True})

    async def check_twitter(self):
        try:
            r = await self.client.get(f"https://api.twitter.com/i/users/email_available.json?email={self.email}", headers=self.get_headers())
            self.results.append({"s": "Twitter", "e": r.json().get("taken", False)})
        except: self.results.append({"s": "Twitter", "e": False, "err": True})

    async def check_adobe(self):
        try:
            h = self.get_headers({"X-IMS-CLIENTID": "adobedotcom2", "Content-Type": "application/json"})
            r = await self.client.post("https://auth.services.adobe.com/signin/v1/authenticationstate", json={"username": self.email, "accountType": "individual"}, headers=h)
            self.results.append({"s": "Adobe", "e": "x-ims-authentication-state-encrypted" in r.headers})
        except: self.results.append({"s": "Adobe", "e": False, "err": True})

    async def check_snapchat(self):
        try:
            res = await self.client.post("https://accounts.snapchat.com/accounts/get_password_strength", data={"email": self.email}, headers=self.get_headers())
            self.results.append({"s": "Snapchat", "e": "associated" in res.text.lower()})
        except: self.results.append({"s": "Snapchat", "e": False, "err": True})

    async def check_github(self):
        try:
            r = await self.client.get(f"https://github.com/signup_check/email?value={self.email}", headers=self.get_headers())
            self.results.append({"s": "GitHub", "e": "taken" in r.text})
        except: self.results.append({"s": "GitHub", "e": False, "err": True})

    async def check_spotify(self):
        try:
            r = await self.client.get(f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={self.email}", headers=self.get_headers())
            self.results.append({"s": "Spotify", "e": r.json().get("status") == 20})
        except: self.results.append({"s": "Spotify", "e": False, "err": True})

    async def check_amazon(self):
        try:
            h = self.get_headers({"Host": "www.amazon.com"})
            r = await self.client.get("https://www.amazon.com/ap/signin?openid.mode=checkid_setup&openid.ns=http://specs.openid.net/auth/2.0", headers=h)
            self.results.append({"s": "Amazon", "e": "email" in r.text and self.email in r.text}) # Simplifié pour PoC
        except: self.results.append({"s": "Amazon", "e": False, "err": True})

    async def check_facebook(self):
        try:
            h = self.get_headers()
            r = await self.client.post("https://www.facebook.com/api/v1/web/accounts/web_create_ajax/attempt/", data={"email": self.email}, headers=h)
            self.results.append({"s": "Facebook", "e": "email_is_taken" in r.text})
        except: self.results.append({"s": "Facebook", "e": False, "err": True})

    async def check_discord(self):
        try:
            r = await self.client.post("https://discord.com/api/v9/auth/register", json={"email": self.email, "username": "audit_user"}, headers=self.get_headers())
            self.results.append({"s": "Discord", "e": "EMAIL_ALREADY_REGISTERED" in r.text})
        except: self.results.append({"s": "Discord", "e": False, "err": True})

    async def check_ebay(self):
        try:
            r = await self.client.post("https://signin.ebay.com/signin/srv/identifer", data={"identifier": self.email}, headers=self.get_headers())
            self.results.append({"s": "eBay", "e": '"err":' not in r.text})
        except: self.results.append({"s": "eBay", "e": False, "err": True})

    async def check_pinterest(self):
        try:
            r = await self.client.get(f"https://www.pinterest.com/_ngjs/resource/EmailExistsResource/get/?data=%7B%22options%22%3A%7B%22email%22%3A%22{self.email}%22%7D%7D", headers=self.get_headers())
            self.results.append({"s": "Pinterest", "e": r.json()["resource_response"]["data"] is True})
        except: self.results.append({"s": "Pinterest", "e": False, "err": True})

    async def check_tumblr(self):
        try:
            r = await self.client.post("https://www.tumblr.com/api/v2/register/account/validate", json={"email": self.email}, headers=self.get_headers())
            self.results.append({"s": "Tumblr", "e": r.json()["response"].get("code") == 2})
        except: self.results.append({"s": "Tumblr", "e": False, "err": True})

    async def check_pornhub(self):
        try:
            r = await self.client.post("https://www.pornhub.com/user/create_account_check", data={"check_what": "email", "email": self.email}, headers=self.get_headers())
            self.results.append({"s": "Pornhub", "e": "taken" in r.text})
        except: self.results.append({"s": "Pornhub", "e": False, "err": True})

    async def run(self):
        print(f"[*] Analyse massive de l'empreinte pour : {self.email}")
        tasks = [
            self.check_instagram(), self.check_twitter(), self.check_adobe(), 
            self.check_snapchat(), self.check_github(), self.check_spotify(),
            self.check_facebook(), self.check_discord(), self.check_ebay(),
            self.check_pinterest(), self.check_tumblr(), self.check_pornhub()
        ]
        await asyncio.gather(*tasks)
        await self.client.aclose()
        self.report()

    def report(self):
        print("\n" + "─"*65)
        for r in sorted(self.results, key=lambda x: x['s']):
            if r.get("err"): print(f" [\033[93m!\033[0m] {r['s'].ljust(18)} : TIMEOUT/ERR")
            else:
                c = "\033[92m" if r['e'] else "\033[91m"
                t = "[+]" if r['e'] else "[-]"
                status = "DETECTE" if r['e'] else "NON TROUVE"
                print(f" {c}{t} {r['s'].ljust(18)} : {status}\033[0m")
        print("─"*65 + f"\nScan terminé en {round(time.time() - self.start_time, 2)}s\n")

if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("email")
    args = p.parse_args()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", args.email): sys.exit("[-] Email invalide")
    asyncio.run(ZeroTraceAuditor(args.email).run())