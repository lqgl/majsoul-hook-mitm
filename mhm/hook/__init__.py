from mhm.proto import MsgManager, MsgType


class Hook:
    def __init__(self) -> None:
        self.mapHook = {}

    def apply(self, mger: MsgManager):
        mKey = (mger.m.type, mger.m.method)
        if mKey in self.mapHook:
            self.mapHook[mKey](mger)

    def bind(self, mType: MsgType, mMethod: str):
        def decorator(func):
            mKey = (mType, mMethod)
            self.mapHook[mKey] = func
            return func

        return decorator