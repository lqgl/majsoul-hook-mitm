# majsoul-hook-mitm

mhm 使用 Proxinject 在雀魂客户端中注入 Socks5 代理

拦截 WebSocket 连接并使用 Protobuf 进行解析

通过修改和转发数据以实现以下功能：

- [x] 兼容小助手
- [x] 本地全皮肤
- [ ] 本地昵称
- [ ] 本地寻觅
- [x] 随机星标皮肤

## 用前须知

> _魔改千万条，安全第一条。_
>
> _使用不规范，账号两行泪。_
>
> _本插件仅供学习参考交流，_
>
> _请使用者于下载 24 小时内自行删除，不得用于商业用途，否则后果自负。_

## 支持平台

- 雀魂客户端

## 使用方法

安装配置 mhm 需求 Python >= 3.10

同步仓库

```bash
git clone https://github.com/anosora233/majsoul-hook-mitm.git && cd majsoul-hook-mitm

```

配置国内镜像源（可选）

```bash
python -m pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
```

安装依赖

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

启动 mhm

```bash
python -m mhm
```

## 配置文件

首次启动 mhm 会自动生成配置文件 mhmp.json

可以编辑此文件以根据需求自定义设置，以下表格解释了 hook 可用的配置选项：

| 释义         | 键               | 可用值        |
| ------------ | ---------------- | ------------- |
| 启用全皮肤   | enable_skins     | true \| false |
| 启用小助手   | enable_aider     | true \| false |
| 启用伪寻觅   | enable_chest     | true \| false |
| 随机星标皮肤 | random_star_char | true \| false |

## 特别感谢

- [Avenshy](https://github.com/Avenshy/mahjong-helper-majsoul-mitmproxy)
- [PragmaTwice](https://github.com/PragmaTwice/proxinject)
- [747929791](https://github.com/747929791/majsoul_wrapper)
- [EndlessCheng](https://github.com/EndlessCheng/mahjong-helper)
