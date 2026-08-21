"""
Coze AI 编程智能体 API 客户端。

调用部署后的 /stream_run 接口，接收 SSE 流式回答。
"""

import json
import os
import uuid
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


load_dotenv()


class CozeAPI:
    """调用部署在 coze.site 上的真实智能体。"""

    def __init__(
        self,
        api_token: Optional[str] = None,
        project_id: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_url = (
            api_url
            or os.getenv("COZE_AGENT_URL")
            or "https://q8jxhkd26s.coze.site/stream_run"
        )

        self.api_token = (
            api_token
            or os.getenv("COZE_AGENT_TOKEN", "")
        )

        self.project_id = (
            project_id
            or os.getenv("COZE_PROJECT_ID", "")
        )

        # 每个 CozeAPI 实例对应一段独立对话
        self.session_id = self._create_session_id()

        if not self.api_token:
            raise ValueError(
                "没有配置 COZE_AGENT_TOKEN，请检查 .env 文件"
            )

        if not self.project_id:
            raise ValueError(
                "没有配置 COZE_PROJECT_ID，请检查 .env 文件"
            )

    @staticmethod
    def _create_session_id() -> str:
        """生成新的 Coze 会话 ID。"""
        return uuid.uuid4().hex

    def reset_session(self):
        """开始一段新对话。"""
        self.session_id = self._create_session_id()

    def chat(
        self,
        message: str,
        stream: bool = False,
        conversation_id: Optional[str] = None,
    ) -> Dict:
        """
        向 Coze 智能体发送用户问题。

        Args:
            message: 用户每次输入的不同问题。
            stream: 为兼容原项目保留，本方法内部始终读取 SSE。
            conversation_id: 为兼容原项目保留。

        Returns:
            {
                "success": bool,
                "response": str,
                "conversation_id": str,
                "error": str
            }
        """
        message = message.strip()

        if not message:
            return {
                "success": False,
                "response": "请输入问题。",
                "conversation_id": self.session_id,
                "error": "empty_message",
            }

        if conversation_id:
            self.session_id = conversation_id

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        payload = {
            "content": {
                "query": {
                    "prompt": [
                        {
                            "type": "text",
                            "content": {
                                # 每次用户输入都会进入这里
                                "text": message
                            },
                        }
                    ]
                }
            },
            "type": "query",
            "session_id": self.session_id,
            "project_id": int(self.project_id),
        }

        answer_parts = []
        error_message = ""

        try:
            with requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=(15, 180),
            ) as response:
                response.encoding = "utf-8"
                response.raise_for_status()

                for line in response.iter_lines(
                    decode_unicode=True
                ):
                    if not line:
                        continue

                    if not line.startswith("data:"):
                        continue

                    data_text = line[5:].strip()

                    if not data_text:
                        continue

                    try:
                        event_data = json.loads(data_text)
                    except json.JSONDecodeError:
                        continue

                    event_type = event_data.get("type")
                    content = event_data.get("content") or {}

                    # Coze 会把回答拆成多个 answer 片段
                    if event_type == "answer":
                        answer_piece = content.get("answer")

                        if answer_piece:
                            answer_parts.append(answer_piece)

                    elif event_type == "error":
                        error_info = content.get("error")

                        if isinstance(error_info, dict):
                            error_message = (
                                error_info.get("message")
                                or json.dumps(
                                    error_info,
                                    ensure_ascii=False,
                                )
                            )
                        elif error_info:
                            error_message = str(error_info)

                    elif event_type == "message_end":
                        end_info = content.get("message_end") or {}

                        code = str(end_info.get("code", "0"))

                        if code != "0":
                            error_message = (
                                end_info.get("message")
                                or f"Coze 执行失败，错误码：{code}"
                            )

            final_answer = "".join(answer_parts).strip()

            if error_message:
                return {
                    "success": False,
                    "response": f"Coze 调用失败：{error_message}",
                    "conversation_id": self.session_id,
                    "error": error_message,
                }

            if not final_answer:
                return {
                    "success": False,
                    "response": "Coze 已完成执行，但没有返回文字回答。",
                    "conversation_id": self.session_id,
                    "error": "empty_answer",
                }

            return {
                "success": True,
                "response": final_answer,
                "conversation_id": self.session_id,
                "error": "",
            }

        except requests.Timeout:
            return {
                "success": False,
                "response": "Coze 响应超时，请稍后重试。",
                "conversation_id": self.session_id,
                "error": "timeout",
            }

        except requests.HTTPError as exc:
            response_text = ""

            if exc.response is not None:
                response_text = exc.response.text[:1000]

            return {
                "success": False,
                "response": (
                    f"Coze HTTP 请求失败：{exc} "
                    f"{response_text}"
                ),
                "conversation_id": self.session_id,
                "error": str(exc),
            }

        except requests.RequestException as exc:
            return {
                "success": False,
                "response": f"无法连接 Coze：{exc}",
                "conversation_id": self.session_id,
                "error": str(exc),
            }

        except Exception as exc:
            return {
                "success": False,
                "response": f"调用 Coze 时发生错误：{exc}",
                "conversation_id": self.session_id,
                "error": str(exc),
            }

    def validate_credentials(self) -> Dict:
        """发送一次测试问题，验证配置。"""
        old_session_id = self.session_id
        self.reset_session()

        result = self.chat("请只回复：连接成功")

        # 验证之后恢复原来的聊天会话
        self.session_id = old_session_id

        if result.get("success"):
            return {
                "valid": True,
                "message": (
                    "Coze 智能体连接成功："
                    f"{result.get('response', '')}"
                ),
            }

        return {
            "valid": False,
            "message": result.get(
                "response",
                "Coze 智能体连接失败",
            ),
        }


def get_coze_client(
    use_mock: bool = False,
    api_key: Optional[str] = None,
    bot_id: Optional[str] = None,
) -> CozeAPI:
    """
    返回真实 Coze 客户端。

    use_mock、api_key 和 bot_id
    仅为兼容原有调用签名而保留。
    """
    return CozeAPI()
