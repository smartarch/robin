from .exceptions import LocationUndefined
import json
import  re
#
# class Parser:
#
#     _name: str = ""
#     _locators: dict = {}
#
#     def __int__(self, name: str, locators: dict) -> None:
#         self._name = name
#         self._locators = locators
#
#     def parse(self, data: {}) -> dict:
#         result = {}
#         for key, locations in self._locators:
#             location_indicators = locations.split('.')
#             assert len(location_indicators) > 0, LocationUndefined.throw(prefix="", message=key, postfix=self._name)
#             # nested locations
#             # for example the 4th author affiliation is in paper.authors.4.affiliation
#             value = data[location_indicators[0]]
#             for location_indicator in location_indicators[1:]:
#                 value = value[location_indicator]
#
#             if isinstance(key, Parser):
#                 result[key._name] = key.parse(value)
#             else:
#                 result[key] = value
#
#         return result


def parse_doi(data: json) -> dict:

    def parse_affiliation(author_affiliation: str) -> dict:
        if author_affiliation:
            code = author_affiliation.split(',')
            if len(code) > 1:
                return {
                    "institute": ", ".join(code[:-1]),
                    "country": {
                        "name": code[-1],
                    }
                }
        return {}

    def try_get(msg: dict, key: str):
        if msg and key in msg:
            return msg[key]
        else:
            return None

    def try_access(msg: list, index: int):
        if msg and index < len(msg):
            return msg[index]
        else:
            return None

    return {
        "title": data["title"],
        "clean_title": re.sub('[^a-zA-Z0-9]+', '', str(data["title"])).lower(),
        "year": data["published"]["date-parts"][0][0] if "published" in data else data["issued"]["date-parts"][0][0],
        "doi": data["DOI"],
        "url": try_get(msg=data, key="URL"),
        "citations": try_get(msg=data, key="is-referenced-by-count"),
        "abstract": try_get(msg=data, key="abstract"),
        "source": try_get(msg=data, key="source"),
        "event": {
            "name": data["container-title"] if "container-title" in data else "NO_EVENT",
            "type": try_get(msg=data, key="type"),
            "publisher": data["publisher"],
            "acronym": try_get(msg=data, key="short-container-title"),
            "volume": try_get(msg=data, key="volume"),
            "number": try_get(msg=data, key="issue"),

        },
        "authors": [{
            "first_name": author["given"],
            "last_name": author["family"],
            "affiliation": parse_affiliation(try_access(try_get(msg=author, key="affiliation"),index=0)),
            }
            for author in data["author"]
        ],

    }


