"""Text analyzer shared by training, candidate checks and saved models."""

from functools import lru_cache
import html
import re
import unicodedata

from janome.tokenizer import Tokenizer


HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
PRIVATE = re.compile(
    r"(?:https?://|www\.)\S+|[\w.+-]+@[\w.-]+\.[a-z]{2,}"
    r"|(?<!\w)@\w+|(?<!\w)\+?\d(?:[(). -]*\d){8,14}(?!\w)", re.I,
)
RATING = re.compile(
    r"(?<!\w)[0-9]+(?:[.,][0-9]+)?\s*(?:/\s*(?:10|5)(?!\d)|"
    r"(?:sao|stars?|étoiles?)(?!\w)|星)|(?:星|評価)\s*[0-5](?!\d)|[★☆⭐]+", re.I,
)
SENTENCE = re.compile(r"[.!?…。！？\n]+")
WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
JA_WORD = re.compile(r"\w+", re.UNICODE)
JA_SCRIPT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
FOREIGN_SCRIPT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
EDGE_WORDS = {
    "vi": ("và thì là mà của vì nhưng nên rồi ở tại với trong để một cái các những tôi mình bạn có", "rất không chưa hơi thật cực được"),
    "en": ("a an the and or but of with in at to for i we they it this that is was were be", "very really too so not quite no"),
    "fr": ("un une le la les des du de et ou mais à au avec pour en je nous c est ce cette", "très trop assez peu bien"),
    "ja": ("の は が を に で と も へ て ね よ から まで だ です ます", "とても かなり あまり すごく"),
}


def clean_text(text):
    text = unicodedata.normalize("NFC", html.unescape(text))
    text = re.sub(r"<(?:br\s*/?|/p|/div|/li)\s*>", "\n", text, flags=re.I)
    text = HTML_TAG.sub(" ", text)
    text = PRIVATE.sub("\n", text)
    text = RATING.sub("\n", text)
    return re.sub(r"[^\S\n]+", " ", text).strip()


@lru_cache(maxsize=1)
def japanese_tokenizer():
    return Tokenizer(wakati=True)


def token_sentences(text, language):
    for sentence in SENTENCE.split(text.lower()):
        if language == "ja":
            tokens = [
                token for token in japanese_tokenizer().tokenize(sentence, wakati=True)
                if JA_WORD.fullmatch(token)
            ]
        else:
            tokens = WORD.findall(sentence)
        if tokens:
            yield tokens


def terms(text, language):
    for tokens in token_sentences(text, language):
        for size in (1, 2, 3):
            for index in range(len(tokens) - size + 1):
                yield " ".join(tokens[index:index + size])


def candidate_text(term, language):
    tokens = term.split()
    function_words, modifiers = map(str.split, EDGE_WORDS[language])
    if not any(character.isalpha() for character in term) or any(character.isdigit() for character in term):
        return False
    if language == "ja" and not JA_SCRIPT.search(term):
        return False
    if language != "ja" and FOREIGN_SCRIPT.search(term):
        return False
    if len(tokens) == 1:
        return term not in function_words + modifiers and (language == "ja" or len(term) > 1)
    return tokens[0] not in function_words and tokens[-1] not in function_words + modifiers


def context_tokens(text, language, term, shop_name):
    if shop_name and len(shop_name.strip()) >= 3:
        text = re.sub(re.escape(shop_name.strip()), "\n", text, flags=re.I)
    text = re.sub(r"\b\d+\b|\b[A-ZÀ-Ỹ][a-zà-ỹ]+(?: +[A-ZÀ-Ỹ][a-zà-ỹ]+)+\b", "\n", text)
    target = term.split()
    for tokens in token_sentences(text, language):
        for index in range(len(tokens) - len(target) + 1):
            if tokens[index:index + len(target)] == target:
                return " ".join(tokens[max(0, index - 4):index + len(target) + 4])
    return ""
