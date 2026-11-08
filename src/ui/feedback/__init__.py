"""反馈类组件：对话框、消息提示、通知、加载、进度条。

- :class:`~ui.feedback.message.Message` —— 主动操作的反馈，顶部居中、自动消失。
- :class:`~ui.feedback.notification.Notification` —— 系统级提醒，贴角、带标题。

门面惰性（见 :mod:`ui._lazy`）：弹出「保存成功」不必先加载对话框与进度条。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "AlertDialog": ".alert_dialog",
        "Loading": ".loading",
        "Message": ".message",
        "Notification": ".notification",
        "ProgressBar": ".progress_bar",
    },
    __name__,
)
