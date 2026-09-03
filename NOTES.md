# NOTES

세션마다 무엇이 헷갈렸고 어떻게 풀렸는지 기록한다.
정식 세션 문서는 `docs/`에 있다.

---

## 코퍼스 출처

`data/`는 `.gitignore`에 있어 커밋되지 않는다. 다른 컴퓨터에서 저장소를 받으면
아래에서 다시 받아야 한다.

| 파일 | 출처 | 검증 |
|---|---|---|
| `data/the-verdict.txt` | Edith Wharton, *The Verdict* (public domain). Raschka 저장소 `ch02/01_main-chapter-code/the-verdict.txt` | 문자 20,479 / 토큰 4,690 / 어휘 1,130 |
| `data/Annabel_Lee.txt` | Edgar Allan Poe, *Annabel Lee* (public domain) | 문자 1,539 / 토큰 330 / 어휘 142 |

검증용:

```python
import re
t = open("data/the-verdict.txt", encoding="utf-8").read()
pre = [i.strip() for i in re.split(r'([,.:;?_!"()\']|--|\s)', t) if i.strip()]
print(len(t), len(pre), len(set(pre)))
```

---

## 2026-09-03 (세션 02)

**the-verdict.txt가 손상되어 있었다.** 줄 끝마다 백슬래시가 붙어 있다(82개).
문단 사이 빈 줄이 복사 과정에서 `\`로 치환된 것으로 보인다.

찾기 어려웠던 이유: 코드가 에러 없이 돌고, 출력도 그럴듯하고, **문자 수가 20,479로
책과 정확히 일치**한다. 개행 82개가 백슬래시 82개로 일대일 치환되면 길이가 안 변한다.
책과 대조해야만 보인다 — 토큰 4,772(책 4,690), 어휘 1,131(책 1,130), 초과분이 정확히 82.

교훈: **출력이 그럴듯하다는 것은 맞다는 뜻이 아니다.** 책이 숫자를 적어둔 이유가 이것이다.

→ 미해결. 다음 세션 첫 작업으로 재취득할 것.

**`KeyError: '"'`.** 어휘는 Annabel Lee에서 만들고 테스트 문장은 the-verdict에서
가져와서 났다. 실수였지만 도착한 지점은 맞다 — 이게 2.4절 `<|unk|>`의 출발점이다.
V1은 "모르는 단어"라는 개념 자체가 없어서, 어휘 밖을 만나면 표현할 방법이 없어 죽는다.

**em dash.** 책의 정규식은 `--`는 알지만 `—`(U+2014)는 모른다.
그래서 Annabel Lee 어휘에 `love—`, `me—`, `sea—`, `Lee—`, `wingèd`가 통째로 들어간다.
`love`와 `love—`는 어휘집에서 완전히 무관한 두 항목이다.
BPE가 이걸 어떻게 다르게 푸는지가 2.5절에서 볼 것.

`\xa0`(non-breaking space)도 섞여 있었는데 파이썬 `re`의 `\s`가 유니코드 공백을
처리해서 문제가 안 됐다. 운이 좋았던 것이지 안전한 게 아니다.
