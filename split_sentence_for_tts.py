import re

def split_sentence_for_tts(text: str) -> list[str]:
    # 1. 改行(\n)で分割
    paragraphs = text.split("\n")

    split_text: list[str] = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue  # 空行はスキップ
        
        # 2. 区切り文字(「。」や「！」、「？」)で分割。カッコ内の文字は区切り文字とみなさない
        sentences = re.split(r'(?<![「『])([。！？]+)(?![」』])', paragraph.strip())

        # 3. 分割された文を分割文字と合わせて結合
        split_text.extend([sentences[i].strip() + sentences[i + 1] for i in range(0, len(sentences) - 1, 2)])

    return split_text


if __name__ == '__main__':
    # テスト
    text = """これはテストの文章です。
        音声合成のために、長すぎる文章を適切な単位で分割します。
        例えば、ここにすごく長い文章が続いていたとしたら、適切な位置で区切る必要がありますね？
        さらに別の例として、とてもとても長い文章がある場合、それを適切に処理しなければなりません！"""

    print(split_sentence_for_tts(text))
