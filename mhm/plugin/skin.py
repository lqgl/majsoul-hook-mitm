from json import load, dump
from os.path import exists
from os import mkdir
from random import choice, randint
from mitmproxy import http

from mhm import ROOT, conf
from mhm.proto.liqi import Plugin, Msg


def _update(dict_a: dict, dict_b: dict, *exclude: str) -> None:
    for key, value in dict_b.items():
        if key not in exclude and key in dict_a:
            dict_a[key] = value


class SkinInfo:
    """Poor implementation of cfg.item_definition"""

    def __init__(self) -> None:
        # 可用头像框
        included_frames = {305529, 305537, 305542, 305545, 305551, 305552} | set(
            range(305520, 305524)
        )

        excluded_items = {305214, 305314, 305526, 305725} | set(
            range(305501, 305556)
        ).difference(included_frames)

        excluded_titles = {
            600030,
            600043,
            # 600017,
            # 600024,
            # 600025,
            # 600029,
            # 600041,
            # 600044,
        } | set(range(600057, 600064))

        # ...
        self.titles = list(set(range(600002, 600082)).difference(excluded_titles))

        self.items = [
            {"item_id": i, "stack": 1}
            for i in set(range(305001, 309000)).difference(excluded_items)
        ]

        self.path = ROOT / "account"

        if not exists(self.path):
            mkdir(self.path)


class SkinPlugin(Plugin):
    skins: dict[int, type["SkinPlugin"]] = dict()
    games: dict[str, dict[str, any]] = dict()
    info: SkinInfo = SkinInfo()

    def __init__(self) -> None:
        self.profile: str = str()
        self.game_uuid: str = str()
        self.original_char: tuple[int, int] = (200001, 400101)

        self.characters: dict[str, any] = {}
        self.commonviews: dict[str, any] = {}

        # default account structure
        self.account: dict[str, any] = {
            "title": 0,
            "nickname": 0,
            "avatar_id": 0,
            "account_id": 0,
            "loading_image": 0,
        }

    @property
    def views(self) -> dict[str, any]:
        return [
            {
                "type": 0,
                "slot": slot["slot"],
                "item_id_list": [],
                "item_id": choice(slot["item_id_list"])
                if slot["type"]
                else slot["item_id"],
            }
            for slot in self.commonviews["views"][self.commonviews["use"]]["values"]
        ]

    @property
    def avatar_frame(self) -> int:
        for slot in self.commonviews["views"][self.commonviews["use"]]["values"]:
            if slot["slot"] == 5:
                return slot["item_id"]
        return 0

    @property
    def random_star_character(self) -> dict[str, any]:
        return (
            self.get_character(choice(self.characters["character_sort"]))
            if self.characters["character_sort"]
            else self.character
        )

    @property
    def random_character(self) -> dict[str, any]:
        return self.get_character(randint(200001, conf["server"]["max_charid"] - 1))

    @property
    def character(self) -> dict[str, any]:
        return self.get_character(self.characters["main_character_id"])

    @property
    def player(self) -> dict[str, any]:
        (
            player := {
                "views": self.views,
                "character": self.character,
                "avatar_frame": self.avatar_frame,
            }
        ).update(self.account)

        return player

    def save(self) -> None:
        with open(self.profile, "w", encoding="utf-8") as f:
            dump(
                {
                    "account": self.account,
                    "characters": self.characters,
                    "commonviews": self.commonviews,
                },
                f,
                ensure_ascii=False,
            )

    def read(self) -> None:
        with open(self.profile, "r", encoding="utf-8") as f:
            dict_conf = load(f)

            self.characters = dict_conf.get("characters")
            self.commonviews = dict_conf.get("commonviews")
            self.account.update(dict_conf.get("account"))

            self.update()

    def get_character(self, charid: int) -> dict:
        assert 200000 < charid < conf["server"]["max_charid"]
        return self.characters["characters"][charid - 200001]

    def init(self) -> None:
        # commonviews
        self.commonviews = {"views": [{}] * 10, "use": 0}
        for i in range(0, 10):
            self.commonviews["views"][i] = {"values": [], "index": i}

        # characters
        self.characters = {
            "characters": [],
            "skins": [],
            "main_character_id": 200001,
            "send_gift_limit": 2,
            "character_sort": [],
            "finished_endings": [],
            "hidden_characters": [],
            "rewarded_endings": [],
            "send_gift_count": 0,
        }

        # 200001 一姬
        # 200002 二姐
        # ......
        # 200075
        for charid in range(200001, conf["server"]["max_charid"]):
            skin = 400000 + (charid - 200000) * 100 + 1
            character = {
                "charid": charid,
                "level": 5,
                "exp": 1,
                "skin": skin,
                "extra_emoji": [],
                "is_upgraded": True,
                "rewarded_level": [],
                "views": [],
            }

            self.characters["characters"].append(character)
            for skin_id in range(skin, skin + 9):
                self.characters["skins"].append(skin_id)

        # sync origin char
        self.characters["main_character_id"] = self.original_char[0]
        self.character["skin"] = self.original_char[1]

        self.save()

    def update(self) -> None:
        # characters
        if len(self.characters["characters"]) == conf["server"]["max_charid"] - 200001:
            return

        for charid in range(
            len(self.characters["characters"]) + 200001,
            conf["server"]["max_charid"],
        ):
            skin = 400000 + (charid - 200000) * 100 + 1
            character = {
                "charid": charid,
                "level": 5,
                "exp": 1,
                "skin": skin,
                "extra_emoji": [],
                "is_upgraded": True,
                "rewarded_level": [],
                "views": [],
            }

            self.characters["characters"].append(character)
            for skin_id in range(skin, skin + 9):
                self.characters["skins"].append(skin_id)

        self.save()

    """
    Notify
    """

    def _lq_NotifyRoomPlayerUpdate_Notify(self, flow: http.HTTPFlow, msg: Msg):
        for player in msg.data["player_list"]:
            if player["account_id"] in self.skins:
                object: SkinPlugin = self.skins[player["account_id"]]
                _update(player, object.account)

    def _lq_NotifyGameFinishRewardV2_Notify(self, flow: http.HTTPFlow, msg: Msg):
        if msg.data.get("main_character"):
            msg.data["main_character"]["level"] = 5

    """
    Request
    """

    def _lq_FastTest_authGame_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 记录当前对局 UUID
        self.game_uuid = msg.data["game_uuid"]

        return True

    def _lq_Lobby_changeMainCharacter_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 修改主角色时
        self.characters["main_character_id"] = msg.data["character_id"]
        self.account["avatar_id"] = self.character["skin"]
        self.save()

        return super().reply(flow, msg)

    def _lq_Lobby_changeCharacterSkin_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 修改角色皮肤时
        self.get_character(msg.data["character_id"])["skin"] = msg.data["skin"]
        self.account["avatar_id"] = self.character["skin"]
        self.save()

        notify = Msg.notify(
            data={
                "update": {
                    "character": {
                        "characters": [self.get_character(msg.data["character_id"])]
                    }
                }
            },
            method=".lq.NotifyAccountUpdate",
        )

        return super().reply(flow, msg, notifys=[notify])

    def _lq_Lobby_updateCharacterSort_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 修改星标角色时
        self.characters["character_sort"] = msg.data["sort"]
        self.save()

        return super().reply(flow, msg)

    def _lq_Lobby_useTitle_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 选择头衔时
        self.account["title"] = msg.data["title"]
        self.save()

        return super().reply(flow, msg)

    def _lq_Lobby_setLoadingImage_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 选择加载图时
        self.account["loading_image"] = msg.data["images"]
        self.save()

        return super().reply(flow, msg)

    def _lq_Lobby_useCommonView_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 选择装扮时
        self.commonviews["use"] = msg.data["index"]
        self.save()

        return super().reply(flow, msg)

    def _lq_Lobby_saveCommonViews_Req(self, flow: http.HTTPFlow, msg: Msg):
        # 修改装扮时
        self.commonviews["views"][msg.data["save_index"]]["values"] = msg.data["views"]
        self.save()

        return super().reply(flow, msg)

    """
    Response
    """

    def _lq_FastTest_authGame_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 进入对局时
        if self.game_uuid in self.games:
            msg.data["players"] = self.games[self.game_uuid]
        else:
            for player in msg.data["players"]:
                # 替换头像，角色、头衔
                if player["account_id"] in self.skins:
                    object: SkinPlugin = self.skins[player["account_id"]]
                    _update(player, object.player)

                    if conf["plugin"]["random_star_char"]:
                        random_char = object.random_star_character
                        player["character"] = random_char
                        player["avatar_id"] = random_char["skin"]
                # 其他玩家报菜名，对机器人无效
                else:
                    player["character"].update(
                        {"level": 5, "exp": 1, "is_upgraded": True}
                    )

                self.games[self.game_uuid] = msg.data["players"]

    def _lq_Lobby_fetchAccountInfo_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 修改状态面板立绘、头衔
        if msg.data["account"]["account_id"] in self.skins:
            object: SkinPlugin = self.skins[msg.data["account"]["account_id"]]
            _update(msg.data["account"], object.account, "loading_image")

    def _lq_Lobby_fetchCharacterInfo_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 全角色数据替换
        msg.data = self.characters

    def _lq_Lobby_fetchAllCommonViews_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 装扮本地数据替换
        msg.data = self.commonviews

    def _lq_Lobby_fetchTitleList_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 添加头衔
        msg.data["title_list"] = self.info.titles

    def _lq_Lobby_fetchBagInfo_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 添加物品
        msg.data["bag"]["items"].extend(self.info.items)

    def _lq_Lobby_fetchRoom_Res(self, flow: http.HTTPFlow, msg: Msg):
        self._lq_Lobby_createRoom_Res(flow, msg)

    def _lq_Lobby_joinRoom_Res(self, flow: http.HTTPFlow, msg: Msg):
        self._lq_Lobby_createRoom_Res(flow, msg)

    def _lq_Lobby_createRoom_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 在加入、获取、创建房间时修改己方头衔、立绘、角色
        if "room" not in msg.data:
            return True
        for person in msg.data["room"]["persons"]:
            if person["account_id"] in self.skins:
                object: SkinPlugin = self.skins[person["account_id"]]
                _update(person, object.account)

    def _lq_Lobby_oauth2Login_Res(self, flow: http.HTTPFlow, msg: Msg):
        self._lq_Lobby_login_Res(flow, msg)

    def _lq_Lobby_emailLogin_Res(self, flow: http.HTTPFlow, msg: Msg):
        self._lq_Lobby_login_Res(flow, msg)

    def _lq_Lobby_login_Res(self, flow: http.HTTPFlow, msg: Msg):
        # 本地配置文件
        self.profile = self.info.path / f"{msg.data['account_id']}.json"

        # 保存原角色、皮肤、昵称
        avatar_id = msg.data["account"]["avatar_id"]
        character_id = (int)((avatar_id - 400000) / 100 + 200000)
        self.original_char = (character_id, avatar_id)

        # 保存原账户信息
        _update(self.account, msg.data["account"])

        if exists(self.profile):
            self.read()
            _update(msg.data["account"], self.account)
        else:
            self.init()

        self.skins[msg.data["account_id"]] = self
