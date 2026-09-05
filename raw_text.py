import urllib.request
import re

url = "https://raw.githubusercontent.com/rasbt/LLMs-from-scratch/main/ch02/01_main-chapter-code/the-verdict.txt"
file_path = "the-verdict.txt"
urllib.request.urlretrieve(url, file_path)

with open(file_path, "r", encoding="utf-8") as f:
    raw_text = f.read()

preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', raw_text)
preprocessed = [item.strip() for item in preprocessed if item.strip()]
all_words = sorted(set(preprocessed))
vocab = {token: integer for integer, token in enumerate(all_words)}


if __name__ == "__main__":          # ← 이 아래는 raw_text.py를 직접 돌릴 때만 실행
    print("Total number of character:", len(raw_text))
    print(len(preprocessed))
    print(preprocessed[:30])
    print(len(all_words))
    for i, item in enumerate(vocab.items()):
        print(item)
        if i >= 30:
            break