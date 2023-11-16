from json import load, dump
from os.path import exists
from os import mkdir
from random import choice, randint

from mhm import root, conf
from mhm.events import listen
from mhm.proto.liqi import Msg, MsgType


def _update(dict_a: dict, dict_b: dict, *exclude: str) -> None:
    for key, value in dict_b.items():
        if key not in exclude and key in dict_a:
            dict_a[key] = value


"""Response"""


@listen(MsgType.Res, ".lq.Lobby.login")
@listen(MsgType.Res, ".lq.Lobby.emailLogin")
@listen(MsgType.Res, ".lq.Lobby.oauth2Login")  # login
def login(msg: Msg):
    skin = Skin.one(msg.account)

    # 配置文件
    skin.profile = skin.info.path / f"{msg.data['account_id']}.json"
    # 保存原角色、皮肤、昵称
    avatar_id = msg.data["account"]["avatar_id"]
    character_id = (int)((avatar_id - 400000) / 100 + 200000)
    skin.original_char = (character_id, avatar_id)

    if exists(skin.profile):
        skin.read()
        _update(msg.data["account"], skin.account)
    else:
        skin.init()
        _update(skin.account, msg.data["account"])

    msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.joinRoom")
@listen(MsgType.Res, ".lq.Lobby.fetchRoom")
@listen(MsgType.Res, ".lq.Lobby.createRoom")  # login
def joinRoom(msg: Msg):
    # 在加入、获取、创建房间时修改己方头衔、立绘、角色
    if "room" not in msg.data:
        return True
    for person in msg.data["room"]["persons"]:
        if skin := Skin.get(person["account_id"]):
            _update(person, skin.account)
            msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.fetchBagInfo")
def fetchBagInfo(msg: Msg):
    # 添加物品
    if skin := Skin.get(msg.account):
        msg.data["bag"]["items"].extend(skin.info.items)
        msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.fetchTitleList")
def fetchTitleList(msg: Msg):
    # 添加头衔
    if skin := Skin.get(msg.account):
        msg.data["title_list"] = skin.info.titles
        msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.fetchAllCommonViews")
def fetchAllCommonViews(msg: Msg):
    # 装扮本地数据替换
    if skin := Skin.get(msg.account):
        msg.data = skin.commonviews
        msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.fetchCharacterInfo")
def fetchCharacterInfo(msg: Msg):
    # 全角色数据替换
    if skin := Skin.get(msg.account):
        msg.data = skin.characters
        msg.amended = True


@listen(MsgType.Res, ".lq.Lobby.fetchAccountInfo")
def fetchAccountInfo(msg: Msg):
    # 修改状态面板立绘、头衔
    if skin := Skin.get(msg.data["account"]["account_id"]):
        _update(msg.data["account"], skin.account, "loading_image")
        msg.amended = True


@listen(MsgType.Res, ".lq.FastTest.authGame")
def authGame(msg: Msg):
    # 进入对局时
    if skin := Skin.get(msg.account):
        if skin.game_uuid in skin.games:
            msg.data["players"] = skin.games[skin.game_uuid]
        else:
            for player in msg.data["players"]:
                # 替换头像，角色、头衔
                if other := Skin.get(player["account_id"]):
                    _update(player, other.player)

                    if conf["plugin"]["random_star_char"]:
                        random_char = other.random_star_character
                        player["character"] = random_char
                        player["avatar_id"] = random_char["skin"]
                # 其他玩家报菜名，对机器人无效
                else:
                    player["character"].update(
                        {"level": 5, "exp": 1, "is_upgraded": True}
                    )

                skin.games[skin.game_uuid] = msg.data["players"]
        msg.amended = True


"""Request"""


@listen(MsgType.Req, ".lq.FastTest.authGame")
def enterGame(msg: Msg):
    # 记录当前对局 UUID
    if skin := Skin.get(msg.account):
        skin.game_uuid = msg.data["game_uuid"]


@listen(MsgType.Req, ".lq.Lobby.changeMainCharacter")
def changeMainCharacter(msg: Msg):
    # 修改主角色时
    if skin := Skin.get(msg.account):
        skin.characters["main_character_id"] = msg.data["character_id"]
        skin.account["avatar_id"] = skin.character["skin"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.changeCharacterSkin")
def changeCharacterSkin(msg: Msg):
    # 修改角色皮肤时
    if skin := Skin.get(msg.account):
        skin.get_character(msg.data["character_id"])["skin"] = msg.data["skin"]
        skin.account["avatar_id"] = skin.character["skin"]
        skin.save()

        msg.notify(
            data={
                "update": {
                    "character": {
                        "characters": [skin.get_character(msg.data["character_id"])]
                    }
                }
            },
            method=".lq.NotifyAccountUpdate",
        ).inject()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.updateCharacterSort")
def updateCharacterSort(msg: Msg):
    # 修改星标角色时
    if skin := Skin.get(msg.account):
        skin.characters["character_sort"] = msg.data["sort"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.useTitle")
def useTitle(msg: Msg):
    # 选择头衔时
    if skin := Skin.get(msg.account):
        skin.account["title"] = msg.data["title"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.modifyNickname")
def modifyNickname(msg: Msg):
    # 修改昵称时
    if skin := Skin.get(msg.account):
        skin.account["nickname"] = msg.data["nickname"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.setLoadingImage")
def setLoadingImage(msg: Msg):
    # 选择加载图时
    if skin := Skin.get(msg.account):
        skin.account["loading_image"] = msg.data["images"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.useCommonView")
def useCommonView(msg: Msg):
    # 选择装扮时
    if skin := Skin.get(msg.account):
        skin.commonviews["use"] = msg.data["index"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@listen(MsgType.Req, ".lq.Lobby.saveCommonViews")
def saveCommonViews(msg: Msg):
    # 修改装扮时
    if skin := Skin.get(msg.account):
        skin.commonviews["views"][msg.data["save_index"]]["values"] = msg.data["views"]
        skin.save()

        msg.drop()
        msg.respond().inject()


"""Notify"""


@listen(MsgType.Notify, ".lq.NotifyRoomPlayerUpdate")
def NotifyRoomPlayerUpdate(msg: Msg):
    # 房间中添加、减少玩家时修改立绘、头衔
    for player in msg.data["player_list"]:
        if skin := Skin.get(player["account_id"]):
            _update(player, skin.account)
            msg.amended = True


@listen(MsgType.Notify, ".lq.NotifyGameFinishRewardV2")
def NotifyGameFinishRewardV2(msg: Msg):
    # 终局结算时，不播放羁绊动画
    if skin := Skin.get(msg.account):
        msg.data["main_character"] = {"exp": 1, "add": 0, "level": 5}
        msg.amended = True


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

        self.path = root / "account"

        if not exists(self.path):
            mkdir(self.path)


class Skin:
    skins: dict[int, type["Skin"]] = dict()
    games: dict[str, dict] = dict()
    info: SkinInfo = SkinInfo()

    @classmethod
    def one(cls, account):
        if account in cls.skins:
            one = cls.skins[account]
        else:
            one = cls.skins[account] = cls()
        return one

    @classmethod
    def get(cls, account_id):
        return cls.skins.get(account_id)

    def __init__(self) -> None:
        self.profile = ""
        self.game_uuid = ""
        self.original_char = (200001, 400101)

        self.characters = {}
        self.commonviews = {}

        # default account structure
        self.account = {
            "title": 0,
            "nickname": 0,
            "avatar_id": 0,
            "account_id": 0,
            "loading_image": 0,
        }

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
    def avatar_frame(self) -> int:
        for slot in self.commonviews["views"][self.commonviews["use"]]["values"]:
            if slot["slot"] == 5:
                return slot["item_id"]
        return 0

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
