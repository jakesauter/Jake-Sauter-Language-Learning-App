"""Video links: only YouTube/Instagram are fetched, long speech is split into study lines, subtitles are read cleanly."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
for heavy_module in ("conversations", "ensemble", "live_session", "translation"):
    sys.modules.setdefault(heavy_module, types.ModuleType(heavy_module))

import pytest  # noqa: E402

import video_import  # noqa: E402


@pytest.mark.parametrize("link", ["https://www.instagram.com/reel/Dc_bYNUSoAG/?x=1", "https://youtu.be/abc", "https://m.youtube.com/watch?v=x"])
def test_allowed_links(link):
    assert video_import.checked_link(link).startswith("https://")


@pytest.mark.parametrize("link", ["http://169.254.169.254/", "https://evil.com/youtube.com", "https://www.youtube.com:444/x",
                                  "file:///etc/passwd", "https://user@youtube.com/", "https://youtube.com.evil.com/"])
def test_refused_links(link):
    with pytest.raises(ValueError):
        video_import.checked_link(link)


def test_long_speech_becomes_sentences_with_shared_times():
    lines = video_import.sentences_of({"text": "生菜你想食咩？你講我聽咩？菠菜幾多錢啊？", "start": 10.0, "end": 16.0})
    assert [line["text"] for line in lines] == ["生菜你想食咩？", "你講我聽咩？", "菠菜幾多錢啊？"]
    assert lines[0]["start"] == 10.0 and lines[-1]["end"] == 16.0


def test_subtitles_drop_markup_and_repeats(tmp_path):
    path = tmp_path / "audio.yue.vtt"
    path.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.500\n<c>你好</c>\n\n00:00:02.500 --> 00:00:03.000\n你好\n\n"
                    "00:01:03.000 --> 00:01:05.000\n食咗飯未\n", encoding="utf-8")
    assert video_import.subtitle_lines(str(path)) == [{"start": 1.0, "end": 3.0, "text": "你好"}, {"start": 63.0, "end": 65.0, "text": "食咗飯未"}]


def test_instagram_title_falls_back_to_caption():
    assert video_import.video_title({"title": "Video by someone", "description": "#hk\nShe was so nice!!\n#canto"}) == "She was so nice!!"
