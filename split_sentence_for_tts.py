import re

def split_sentence_for_tts(text, max_length=100):
    # 1. 改行(\n)で分割
    paragraphs = text.split("\n")

    split_text = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue  # 空行はスキップ
        
        # 2. 「。」や「！」、「？」で分割
        sentences = re.split(r'([。！？])', paragraph.strip())
        chunks = []
        temp = ""

        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + sentences[i+1]
            if len(temp) + len(sentence) > max_length:
                if temp:
                    chunks.append(temp)
                temp = sentence
            else:
                temp += sentence

        if temp:
            chunks.append(temp)

        # 3. さらに「、」で分割
        refined_chunks = []
        for chunk in chunks:
            if len(chunk) > max_length:
                parts = re.split(r'(、)', chunk)  # 読点で分割
                temp = ""
                for i in range(0, len(parts)-1, 2):
                    part = parts[i] + parts[i+1]
                    if len(temp) + len(part) > max_length:
                        if temp:
                            refined_chunks.append(temp)
                        temp = part
                    else:
                        temp += part
                if temp:
                    refined_chunks.append(temp)
            else:
                refined_chunks.append(chunk)

        # 4. それでも長い場合は強制カット
        final_chunks = []
        for chunk in refined_chunks:
            while len(chunk) > max_length:
                idx = chunk[:max_length].rfind("、")  # 可能なら読点で区切る
                if idx == -1:
                    idx = max_length  # 読点がない場合は強制カット
                final_chunks.append(chunk[:idx+1])
                chunk = chunk[idx+1:].lstrip()
            if chunk:
                final_chunks.append(chunk)

        split_text.extend(final_chunks)

    return split_text


if __name__ == '__main__':
    # テスト
    text = """これはテストの文章です。
        音声合成のために、長すぎる文章を適切な単位で分割します。
        例えば、ここにすごく長い文章が続いていたとしたら、適切な位置で区切る必要がありますね？
        さらに別の例として、とてもとても長い文章がある場合、それを適切に処理しなければなりません！"""

    print(split_sentence_for_tts(text, max_length=50))
