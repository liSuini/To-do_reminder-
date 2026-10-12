# -*- coding: utf-8 -*-
"""生产适配器：Windows 原生 Toast（winotify，原型验证通过）"""
from winotify import Notification, audio


class WinotifyNotifier:
    """实现 Notifier 接缝的 winotify 适配器（send(title, body)）"""

    def send(self, title: str, body: str):
        toast = Notification(
            app_id="待办助手",
            title=title,
            msg=body,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
