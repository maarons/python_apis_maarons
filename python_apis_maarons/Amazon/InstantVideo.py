import urllib.parse
from urllib.request import urlopen, URLError
import xml.dom.minidom as minidom
from datetime import datetime
import hmac
import hashlib
import base64
import json

import python_apis_maarons.Amazon.xml_to_json as xml_to_json
import python_apis_maarons.Amazon.util as util

class Image():
    def __init__(self, json):
        self.width = json["Width"]["value"]
        self.height = json["Height"]["value"]
        self.url = json["URL"]

    def to_json(self):
        return {
            "width": self.width,
            "height": self.height,
            "url": self.url,
        }

    def __str__(self):
        return json.dumps(self.to_json())

class Episode():
    def __init__(self, json):
        self.title = json["ItemAttributes"]["Title"]
        self.hd = self.title.endswith("[HD]")
        self.url = json["DetailPageURL"]
        img_sizes = [
            ("SmallImage", "small", ),
            ("MediumImage", "medium", ),
            ("LargeImage", "large", ),
        ]
        self.images = {}
        for img_size in img_sizes:
            if img_size[0] in json:
                self.images[img_size[1]] = Image(json[img_size[0]])

    def to_json(self):
        json = {
            "hd": self.hd,
            "url": self.url,
            "images": {}
        }
        for image_size in self.images:
            json["images"][image_size] = self.images[image_size].to_json()
        return json

    def __str__(self):
        return json.dumps(self.to_json())

class AmazonInstantVideo():
    def __init__(self, key_id, secret):
        self.key_id = key_id
        self.secret = secret

    def __sign_request(self, data):
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        data["Timestamp"] = timestamp
        data["AWSAccessKeyId"] = self.key_id
        data["Service"] = "AWSECommerceService"
        data["AssociateTag"] = "MOO"

        params = []
        keys = list(map(lambda s: s.encode("utf-8"), data.keys()))
        keys.sort()
        for key in keys:
            key = key.decode("utf-8")
            value = data[key]
            value = urllib.parse.quote(value, safe = "_-.~")
            params.append("{}={}".format(key, value))
        params = "&".join(params)

        to_sign = "\n".join([
            "GET",
            "webservices.amazon.com",
            "/onca/xml",
            params
        ])

        signature = hmac.new(
            self.secret.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = base64.encodebytes(signature).decode("utf-8").strip()
        params += "&Signature=" + urllib.parse.quote(signature, safe = "_-.~")

        return "http://webservices.amazon.com/onca/xml?" + params

    def __make_request(self, data):
        url = self.__sign_request(data)
        try:
            response = urlopen(url)
        except URLError:
            return None
        return minidom.parseString(response.read())

    # Episode number is not used because omitting it yields better results.
    def search(self, title, season, episode, episode_title):
        data = {
            "Operation": "ItemSearch",
            "SearchIndex": "Video",
            "ResponseGroup": "Small,Images",
            "Keywords": "{} season {} {}".format(
                title,
                season,
                episode_title,
            ),
        }
        xml = self.__make_request(data)
        if xml is None:
            return []
        json = xml_to_json.toJSON(xml)
        items = json["ItemSearchResponse"]["Items"].get("Item", [])
        episodes = []
        for episode in list(map(Episode, util.mkarray(items))):
            if episode.title.lower().find(episode_title.lower()) != -1:
                episodes.append(episode)
        return episodes
