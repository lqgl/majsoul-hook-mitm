from json import load, dump
from os.path import exists
from os import mkdir
from random import choice

from mhm import root, conf
from mhm.events import manager, pool
from mhm.proto.liqi import Msg, MsgType


def _character(charid: int) -> dict:
    return {
        "charid": charid,
        "level": 5,
        "exp": 1,
        "skin": charid % 1000 * 100 + 400001,
        "extra_emoji": [],
        "is_upgraded": True,
        "rewarded_level": [],
        "views": [],
    }


def _characters_and_skins(charid_x: int, charid_y: int):
    characters = [_character(i) for i in range(charid_x, charid_y)]
    skins = [idx for c in characters for idx in range(c["skin"], c["skin"] + 9)]

    return characters, skins


"""Response"""


@manager.register(MsgType.Res, ".lq.Lobby.login")
@manager.register(MsgType.Res, ".lq.Lobby.emailLogin")
@manager.register(MsgType.Res, ".lq.Lobby.oauth2Login")  # login
def login(msg: Msg):
    skin = pool.one(Skin, msg.account, msg)
    skin.update_player(msg.data.get("account"))
    msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.joinRoom")
@manager.register(MsgType.Res, ".lq.Lobby.fetchRoom")
@manager.register(MsgType.Res, ".lq.Lobby.createRoom")  # login
def joinRoom(msg: Msg):
    # 在加入、获取、创建房间时修改己方头衔、立绘、角色
    if "room" not in msg.data:
        return True
    for person in msg.data["room"]["persons"]:
        if skin := pool.get(Skin, person["account_id"]):
            skin.update_player(person)
            msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.fetchBagInfo")
def fetchBagInfo(msg: Msg):
    # 添加物品
    if skin := pool.get(Skin, msg.account):
        msg.data["bag"]["items"].extend(skin.info.items)
        msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.fetchTitleList")
def fetchTitleList(msg: Msg):
    # 添加头衔
    if skin := pool.get(Skin, msg.account):
        msg.data["title_list"] = skin.info.titles
        msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.fetchAllCommonViews")
def fetchAllCommonViews(msg: Msg):
    # 装扮本地数据替换
    if skin := pool.get(Skin, msg.account):
        msg.data = skin.commonviews
        msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.fetchCharacterInfo")
def fetchCharacterInfo(msg: Msg):
    # 全角色数据替换
    if skin := pool.get(Skin, msg.account):
        msg.data = skin.characterinfo
        msg.amended = True


@manager.register(MsgType.Res, ".lq.Lobby.fetchAccountInfo")
def fetchAccountInfo(msg: Msg):
    # 修改状态面板立绘、头衔
    if skin := pool.get(Skin, msg.data["account"]["account_id"]):
        skin.update_player(msg.data["account"], "loading_image")
        msg.amended = True


@manager.register(MsgType.Res, ".lq.FastTest.authGame")
def authGame(msg: Msg):
    # 进入对局时
    if skin := pool.get(Skin, msg.account):
        msg.data["players"] = pool.one(GameInfo, skin.game_uuid, msg.data["players"])
        msg.amended = True


"""Request"""


@manager.register(MsgType.Req, ".lq.FastTest.authGame")
def authGame(msg: Msg):
    # 记录当前对局 UUID
    if skin := pool.get(Skin, msg.account):
        skin.game_uuid = msg.data["game_uuid"]


@manager.register(MsgType.Req, ".lq.Lobby.changeMainCharacter")
def changeMainCharacter(msg: Msg):
    # 修改主角色时
    if skin := pool.get(Skin, msg.account):
        skin.main_character_id = msg.data["character_id"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.changeCharacterSkin")
def changeCharacterSkin(msg: Msg):
    # 修改角色皮肤时
    if skin := pool.get(Skin, msg.account):
        character = skin.character_of(msg.data["character_id"])
        character["skin"] = msg.data["skin"]
        skin.save()

        msg.notify(
            data={"update": {"character": {"characters": [character]}}},
            method=".lq.NotifyAccountUpdate",
        ).inject()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.updateCharacterSort")
def updateCharacterSort(msg: Msg):
    # 修改星标角色时
    if skin := pool.get(Skin, msg.account):
        skin.characterinfo["character_sort"] = msg.data["sort"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.useTitle")
def useTitle(msg: Msg):
    # 选择头衔时
    if skin := pool.get(Skin, msg.account):
        skin.title = msg.data["title"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.modifyNickname")
def modifyNickname(msg: Msg):
    # 修改昵称时
    if skin := pool.get(Skin, msg.account):
        skin.nickname = msg.data["nickname"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.setLoadingImage")
def setLoadingImage(msg: Msg):
    # 选择加载图时
    if skin := pool.get(Skin, msg.account):
        skin.loading_image = msg.data["images"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.useCommonView")
def useCommonView(msg: Msg):
    # 选择装扮时
    if skin := pool.get(Skin, msg.account):
        skin.use = msg.data["index"]
        skin.save()

        msg.drop()
        msg.respond().inject()


@manager.register(MsgType.Req, ".lq.Lobby.saveCommonViews")
def saveCommonViews(msg: Msg):
    # 修改装扮时
    if skin := pool.get(Skin, msg.account):
        skin.commonviews["views"][msg.data["save_index"]]["values"] = msg.data["views"]
        skin.save()

        msg.drop()
        msg.respond().inject()


"""Notify"""


@manager.register(MsgType.Notify, ".lq.NotifyRoomPlayerUpdate")
def NotifyRoomPlayerUpdate(msg: Msg):
    # 房间中添加、减少玩家时修改立绘、头衔
    for player in msg.data["player_list"]:
        if skin := pool.get(Skin, player["account_id"]):
            skin.update_player(player)
            msg.amended = True


@manager.register(MsgType.Notify, ".lq.NotifyGameFinishRewardV2")
def NotifyGameFinishRewardV2(msg: Msg):
    # 终局结算时，不播放羁绊动画
    if skin := pool.get(Skin, msg.account):
        msg.data["main_character"] = {"exp": 1, "add": 0, "level": 5}
        msg.amended = True


class Skin:
    @property
    def use(self) -> int:
        return self.commonviews["use"]

    @use.setter
    def use(self, value: int):
        self.commonviews["use"] = value

    @property
    def main_character_id(self) -> int:
        return self.characterinfo["main_character_id"]

    @main_character_id.setter
    def main_character_id(self, value: int):
        self.characterinfo["main_character_id"] = value

    @property
    def slots(self) -> list[dict]:
        return self.commonviews["views"][self.use].get("values", [])

    @property
    def views(self) -> dict:
        return [
            {
                "type": 0,
                "slot": slot["slot"],
                "item_id_list": [],
                "item_id": choice(slot["item_id_list"])
                if slot["type"]
                else slot["item_id"],
            }
            for slot in self.slots
        ]

    @property
    def avatar_frame(self) -> int:
        for slot in self.slots:
            if slot["slot"] == 5:
                return slot["item_id"]
        return 0

    @property
    def character(self) -> dict:
        return self.character_of(self.main_character_id)

    @property
    def random_star_character_and_skin(self) -> tuple[dict, int]:
        if self.characterinfo["character_sort"]:
            character = self.character_of(choice(self.characterinfo["character_sort"]))
        else:
            character = self.character
        return character, character.get("skin")

    @property
    def avatar_id(self) -> int:
        return self.character["skin"]

    def __init__(self, msg: Msg) -> None:
        self.info = info
        self.path = self.info.root / "{}.json".format(msg.account)

        # base attributes
        self.keys = ["title", "nickname", "loading_image"]
        self.title: int = None
        self.nickname: str = None
        self.loading_image: list = None

        # temp attributes
        self.game_uuid: str = None

        self.update_self(msg.data.get("account"))

        if exists(self.path):
            self.load()
        else:
            self.init()

    def character_of(self, charid: int) -> dict:
        assert 200000 < charid < conf.server.max_charid
        return self.characterinfo["characters"][charid - 200001]

    def update_self(self, player: dict):
        for key in player:
            if key in self.keys:
                setattr(self, key, player[key])

    def update_player(self, player: dict, *exclude: str):
        for key in player:
            if key not in exclude and hasattr(self, key):
                player[key] = getattr(self, key)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            data = {
                "base": {k: getattr(self, k) for k in self.keys},
                "commonviews": self.commonviews,
                "characterinfo": self.characterinfo,
            }

            dump(data, f, ensure_ascii=False)

    def load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data: dict = load(f)

            base = data.get("base", data.get("account"))
            self.commonviews = data.get("commonviews")
            self.characterinfo = data.get("characterinfo", data.get("characters"))

            for key in self.keys:
                setattr(self, key, base[key])

            self.update_characterinfo()

    def init(self):
        # commonviews
        self.commonviews = {
            "views": [{"values": [], "index": i} for i in range(0, 10)],
            "use": 0,
        }

        # characterinfo
        main_character_id = 200001
        characters, skins = _characters_and_skins(200001, conf.server.max_charid)

        self.characterinfo = {
            "characters": characters,
            "skins": skins,
            "main_character_id": main_character_id,
            "send_gift_limit": 2,
            "character_sort": [],
            "finished_endings": [],
            "hidden_characters": [],
            "rewarded_endings": [],
            "send_gift_count": 0,
        }

        # save
        self.save()

    def update_characterinfo(self):
        max = 200001 + len(self.characterinfo.get("characters"))

        if max < conf.server.max_charid:
            characters, skins = _characters_and_skins(max, conf.server.max_charid)

            self.characterinfo.get("characters").extend(characters)
            self.characterinfo.get("skins").extend(skins)
            self.save()


class GameInfo(list):
    def __init__(self, players: list[dict]):
        for player in players:
            if skin := pool.get(Skin, player["account_id"]):
                # 替换对局头像，角色、头衔
                skin.update_player(player)

                if conf.plugin.random_star_char:
                    (
                        player["character"],
                        player["avatar_id"],
                    ) = skin.random_star_character_and_skin
            else:
                # 其他玩家报菜名，对机器人无效
                player["character"].update({"level": 5, "exp": 1, "is_upgraded": True})
        super().__init__(players)


class SkinInfo:
    """Poor implementation of cfg.item_definition"""

    def __init__(self) -> None:
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

        self.titles = list(set(range(600002, 600082)).difference(excluded_titles))

        self.items = [
            {"item_id": i, "stack": 1}
            for i in set(range(305001, 309000)).difference(excluded_items)
        ]

        self.root = root / "account"

        if not exists(self.root):
            mkdir(self.root)


info = SkinInfo()
