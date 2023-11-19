import base64

from struct import unpack, pack
from enum import Enum
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message
from mitmproxy.http import HTTPFlow
from mitmproxy import ctx
from dataclasses import dataclass

from . import liqi_pb2 as pb


""" 
    # msg_block notify
    [   {'id': 1, 'type': 'string','data': b'.lq.ActionPrototype'},
        {'id': 2, 'type': 'string','data': b'protobuf_bytes'}       ]
    # msg_block request & response
    [   {'id': 1, 'type': 'string','data': b'.lq.FastTest.authGame'},
        {'id': 2, 'type': 'string','data': b'protobuf_bytes'}       ]
"""


class MsgType(Enum):
    """Game websocket message type"""

    Notify = 1
    Req = 2
    Res = 3


@dataclass
class Msg:
    """Game websocket message struct"""

    proto: Message
    flow: HTTPFlow
    type: MsgType
    data: dict
    method: str

    id: int = -1
    amended: bool = False

    def __post_init__(self):
        self.key = (self.type, self.method)

    @property
    def compose(self):
        head = self.type.value.to_bytes(length=1, byteorder="little")
        proto_obj = ParseDict(js_dict=self.data, message=self.proto)
        msg_block = [{"id": 1, "type": "string"}, {"id": 2, "type": "string"}]

        if self.type == MsgType.Notify:
            if "data" in self.data:
                """Not yet supported"""
                raise NotImplementedError

            msg_block[0]["data"] = self.method.encode()
            msg_block[1]["data"] = proto_obj.SerializeToString()
            return head + toProtobuf(msg_block)
        elif self.type == MsgType.Req:
            msg_block[0]["data"] = self.method.encode()
            msg_block[1]["data"] = proto_obj.SerializeToString()
            return head + pack("<H", self.id) + toProtobuf(msg_block)
        elif self.type == MsgType.Res:
            msg_block[0]["data"] = b""
            msg_block[1]["data"] = proto_obj.SerializeToString()
            return head + pack("<H", self.id) + toProtobuf(msg_block)

    @property
    def account(self) -> int | None:
        try:
            return getattr(self.flow, "account")
        except AttributeError:
            return None

    @account.setter
    def account(self, account):
        setattr(self.flow, "account", account)

    @property
    def tag(self):
        if tag := self.account:
            return str(tag)
        else:
            return self.flow.id[:13]

    @property
    def message(self):
        return self.flow.websocket.messages[-1]

    def inject(self):
        # inject.websocket flow to_client message is_text
        ctx.master.commands.call(
            "inject.websocket", self.flow, True, self.compose, False
        )  # to_client is always true for security reasons

    def apply(self):
        """Apply amended msg into flow"""
        self.message.content = self.compose

    def drop(self):
        """Drop this message"""
        self.message.drop()

    def notify(self, data: dict, method: str):
        prototype = getPrototype(method, MsgType.Notify)
        return Msg(prototype(), self.flow, MsgType.Notify, data, method)

    def request(self, data: dict = {}):
        assert self.type is MsgType.Res
        prototype, _ = getPrototype(self.method, MsgType.Req)
        return Msg(prototype(), self.flow, MsgType.Req, data, self.method, self.id)

    def respond(self, data: dict = {}):
        assert self.type is MsgType.Req
        _, prototype = getPrototype(self.method, MsgType.Res)
        return Msg(prototype(), self.flow, MsgType.Res, data, self.method, self.id)


class Proto:
    def __init__(self) -> None:
        self.tot = 0
        self.res_type = dict()

    def parse(self, flow: HTTPFlow) -> Msg:
        flow_msg = flow.websocket.messages[-1]
        buf = flow_msg.content
        msg_type = MsgType(buf[0])

        if msg_type == MsgType.Notify:
            msg_block = fromProtobuf(buf[1:])
            method_name = msg_block[0]["data"].decode()
            prototype = getPrototype(method_name, msg_type)
            proto_obj = prototype.FromString(msg_block[1]["data"])
            dict_obj = MessageToDict(
                proto_obj,
                preserving_proto_field_name=True,
                including_default_value_fields=True,
            )

            if "data" in dict_obj:
                B = base64.b64decode(dict_obj["data"])
                action_proto_obj = getattr(pb, dict_obj["name"]).FromString(decode(B))
                action_dict_obj = MessageToDict(
                    action_proto_obj,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True,
                )
                dict_obj["data"] = action_dict_obj

            msg_id = self.tot
        else:
            msg_id = unpack("<H", buf[1:3])[0]
            msg_block = fromProtobuf(buf[3:])
            if msg_type == MsgType.Req:
                assert msg_id < 1 << 16
                assert len(msg_block) == 2
                assert msg_id not in self.res_type
                method_name = msg_block[0]["data"].decode()
                prototype, res_prototype = getPrototype(method_name, msg_type)
                proto_obj = prototype.FromString(msg_block[1]["data"])
                dict_obj = MessageToDict(
                    proto_obj,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True,
                )

                self.res_type[msg_id] = (
                    method_name,
                    res_prototype,
                )
            elif msg_type == MsgType.Res:
                assert len(msg_block[0]["data"]) == 0
                assert msg_id in self.res_type
                method_name, prototype = self.res_type.pop(msg_id)
                proto_obj = prototype.FromString(msg_block[1]["data"])
                dict_obj = MessageToDict(
                    proto_obj,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True,
                )

                if "game_restore" in dict_obj:
                    for action in dict_obj["game_restore"]["actions"]:
                        b64 = base64.b64decode(action["data"])
                        action_proto_obj = getattr(pb, action["name"]).FromString(b64)
                        action_dict_obj = MessageToDict(
                            action_proto_obj,
                            preserving_proto_field_name=True,
                            including_default_value_fields=True,
                        )
                        action["data"] = action_dict_obj
        self.tot += 1
        return Msg(proto_obj, flow, msg_type, dict_obj, method_name, msg_id)


def getPrototype(
    method_name: str, msg_type: MsgType
) -> type[Message] | tuple[type[Message], type[Message]]:
    if msg_type == MsgType.Notify:
        _, lq, message_name = method_name.split(".")
        return getattr(pb, message_name)

    else:
        _, lq, service, rpc = method_name.split(".")
        method_desc = pb.DESCRIPTOR.services_by_name[service].methods_by_name[rpc]

        return (
            getattr(pb, method_desc.input_type.name),
            getattr(pb, method_desc.output_type.name),
        )


def fromProtobuf(buf) -> list[dict]:
    p = 0
    result = []
    while p < len(buf):
        block_begin = p
        block_type = buf[p] & 7
        block_id = buf[p] >> 3
        p += 1
        if block_type == 0:
            block_type = "varint"
            data, p = parseVarint(buf, p)
        elif block_type == 2:
            block_type = "string"
            s_len, p = parseVarint(buf, p)
            data = buf[p : p + s_len]
            p += s_len
        else:
            raise Exception("unknow type:", block_type, "at", p)
        result.append(
            {"id": block_id, "type": block_type, "data": data, "begin": block_begin}
        )
    return result


def toProtobuf(data: list[dict]) -> bytes:
    result = b""
    for d in data:
        if d["type"] == "varint":
            result += ((d["id"] << 3) + 0).to_bytes(length=1, byteorder="little")
            result += toVarint(d["data"])
        elif d["type"] == "string":
            result += ((d["id"] << 3) + 2).to_bytes(length=1, byteorder="little")
            result += toVarint(len(d["data"]))
            result += d["data"]
        else:
            raise NotImplementedError
    return result


def parseVarint(buf, p):
    data = 0
    base = 0
    while p < len(buf):
        data += (buf[p] & 127) << base
        base += 7
        p += 1
        if buf[p - 1] >> 7 == 0:
            break
    return (data, p)


def toVarint(x: int) -> bytes:
    data = 0
    base = 0
    length = 0
    if x == 0:
        return b"\x00"
    while x > 0:
        length += 1
        data += (x & 127) << base
        x >>= 7
        if x > 0:
            data += 1 << (base + 7)
        base += 8
    return data.to_bytes(length, "little")


def decode(data: bytes):
    keys = [0x84, 0x5E, 0x4E, 0x42, 0x39, 0xA2, 0x1F, 0x60, 0x1C]
    data = bytearray(data)
    for i in range(len(data)):
        u = (23 ^ len(data)) + 5 * i + keys[i % len(keys)] & 255
        data[i] ^= u
    return bytes(data)
