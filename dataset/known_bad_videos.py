"""Videos that must stay out of training and testing, each with the reason. Found by reading what the models heard."""

# Subtitles that are not a transcript of the speech.
NOT_CANTONESE_SPEECH = {
    "aRjfEC3KXJ4",  # a Taiwanese food vlog: Mandarin and Hokkien speech with Cantonese-translated subtitles
}

# Lyrics, not conversation.
SONGS = {"wFvPC9eaeLE"}

LEAVE_OUT = NOT_CANTONESE_SPEECH | SONGS
