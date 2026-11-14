"""No network, no LLM: python test_bot.py"""
import os, tempfile
os.environ["DB_DIR"] = tempfile.mkdtemp()
from app import bot

# Markdown splits by heading, so citations read "faq.md › Returns".
secs = bot.sections("intro\n## Shipping\nfree over $35\n## Returns\n30 days\n")
assert [h for h, _ in secs] == ["", "Shipping", "Returns"], secs
assert "30 days" in secs[2][1]
assert bot.chunk("a " * 1000) and all(len(c) <= bot.CHUNK_CHARS for c in bot.chunk("a " * 1000))


class Boom:  # any LLM call fails the test
    def __getattr__(self, _): raise AssertionError("LLM was called despite low relevance")


bot.llm = Boom()
bot.retrieve = lambda q: [{"text": "x", "source": "faq.md", "location": "Shipping", "score": bot.MIN_SCORE - 0.01}]
r = bot.ask("Do you sell gift cards?")
assert r == {"answer": bot.NOT_FOUND, "sources": [], "gated": True}, r
print("ok")
