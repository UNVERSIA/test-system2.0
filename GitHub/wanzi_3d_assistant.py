"""烷仔桌面萌宠与悬浮 Coze 对话组件。"""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from coze_api import get_coze_client


MODULE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = MODULE_DIR / "wanzi_assistant_component" / "frontend"
DEFAULT_MODEL_PATH = MODULE_DIR / "assets" / "models" / "wanzi_web.glb"

_wanzi_component = components.declare_component(
    "wanzi_desktop_assistant",
    path=str(FRONTEND_DIR),
)


@st.cache_data(show_spinner=False)
def _read_model_data_uri(path: str, modified_ns: int, size: int) -> str:
    """将 GLB 缓存为 data URI，浏览器无需访问本地文件路径。"""
    del modified_ns, size
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:model/gltf-binary;base64,{encoded}"


def _init_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "coze_client" not in st.session_state:
        st.session_state.coze_client = None
    if "wanzi_last_event_id" not in st.session_state:
        st.session_state.wanzi_last_event_id = ""


def _get_client():
    if st.session_state.coze_client is None:
        st.session_state.coze_client = get_coze_client()
    return st.session_state.coze_client


def _save_to_existing_history(role: str, content: str) -> None:
    manager = st.session_state.get("chat_history_manager")
    if manager is not None:
        try:
            manager.add_message(role, content)
        except Exception as exc:
            print(f"[Wanzi3D] 保存历史记录失败: {exc}")


def _append_message(role: str, content: str) -> None:
    st.session_state.chat_messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
    )
    _save_to_existing_history(role, content)


def _handle_event(event: Any) -> bool:
    """处理组件事件；返回是否需要立即重新渲染组件。"""
    if not isinstance(event, dict):
        return False

    event_id = str(event.get("id", ""))
    event_type = str(event.get("type", ""))
    if not event_id or event_id == st.session_state.wanzi_last_event_id:
        return False

    st.session_state.wanzi_last_event_id = event_id

    if event_type == "send":
        text = str(event.get("text", "")).strip()
        if not text:
            return False

        _append_message("user", text)
        try:
            result = _get_client().chat(text)
            answer = str(
                result.get("response")
                or "抱歉，我暂时没有获得有效回答，请稍后再试。"
            )
        except Exception as exc:
            print(f"[Wanzi3D] Coze 请求失败: {exc}")
            answer = "连接智能体时出现问题，请稍后重试。"

        _append_message("assistant", answer)
        return True

    if event_type == "clear":
        st.session_state.chat_messages = []
        manager = st.session_state.get("chat_history_manager")
        if manager is not None:
            try:
                manager.clear_history()
            except Exception:
                pass
        if st.session_state.coze_client is not None:
            try:
                st.session_state.coze_client.reset_session()
            except Exception:
                pass
        return True

    return False


def render_wanzi_3d_assistant(
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> None:
    """挂载：悬浮球 → 3D 烷仔 → 悬浮对话窗。"""
    _init_state()
    path = Path(model_path).resolve()

    if not path.is_file():
        print(f"[Wanzi3D] 模型不存在：{path}")
        return
    if not (FRONTEND_DIR / "index.html").is_file():
        print(f"[Wanzi3D] 组件页面不存在：{FRONTEND_DIR / 'index.html'}")
        return

    stat = path.stat()
    model_uri = _read_model_data_uri(
        str(path), stat.st_mtime_ns, stat.st_size
    )

    event = _wanzi_component(
        model_uri=model_uri,
        messages=st.session_state.chat_messages,
        greeting="你好呀，我是烷仔！有什么污水处理问题都可以问我。",
        key="wanzi_desktop_assistant_v2",
        default=None,
    )

    if _handle_event(event):
        st.rerun()
