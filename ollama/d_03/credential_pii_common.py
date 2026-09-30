"""자격증명/PII 예제가 함께 사용하는 더미 패턴 탐지와 마스킹 함수.

이 모듈은 요청을 보내거나 결과를 판정하지 않는다. 두 경로가 같은 규칙으로
민감 패턴을 찾고, 보안 경로가 전송 전에 해당 패턴을 치환할 때 사용한다.
"""

from __future__ import annotations

import re


# 이 실습에 들어 있는 더미 API 키와 이메일 패턴만 찾는다.
# 첫 정규식은 sk- 접두사의 키 형식을, 두 번째는 단순 이메일 형식을 대상으로 한다.
# 따라서 모든 종류의 자격증명·PII를 탐지하는 범용 DLP 규칙은 아니다.
_API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def find_sensitive(text: str) -> list[str]:
    """텍스트에서 이 실습의 API 키/이메일 패턴을 찾아 반환한다.

    반환 목록은 시뮬레이션 근거와 실제 모델 응답 관찰에 사용한다.
    빈 목록은 이 두 패턴이 없다는 뜻이지, 다른 형태의 민감정보가 없다는 보장은 아니다.
    """
    # 각각의 정규식 결과를 합쳐 호출부가 한 번에 확인할 수 있게 한다.
    return _API_KEY_PATTERN.findall(text) + _EMAIL_PATTERN.findall(text)


def redact(text: str) -> str:
    """전송 전 알려진 API 키와 이메일을 교육용 자리표시자로 치환한다.

    입력 문자열 자체는 변경하지 않고 치환된 새 문자열을 반환한다.
    패턴 밖의 비밀 값이나 새로운 키 형식은 이 간단한 규칙으로 제거되지 않는다.
    """
    # 키와 이메일을 별도 표식으로 바꿔 입력 구조는 유지하면서 실제 더미 값을 제거한다.
    text = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)
    return _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
