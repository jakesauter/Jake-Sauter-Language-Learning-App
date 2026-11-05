PHRASES = [

    dict(
        cat = "Road Trip",
        en = "How much longer until we get there?",
        gloss = ["How long", "still / more", "until", "arrive", "(question tone)"],
        yue = [("仲有", "zung6 jau5", [1]), ("幾耐", "gei2 noi6", [0]), ("先", "sin1", [2]), ("到", "dou3", [3]), ("呀", "aa3", [4])],
        cmn = [("还要", "hái yào", [1]), ("多久", "duō jiǔ", [0]), ("才", "cái", [2]), ("到", "dào", [3])],
        tip = "All three put \"still\" before \"how long\", then a word for \"only then\": 先 sin1 in Cantonese, 才 cái in Mandarin. 呀 aa3 softens the question.",
    ),

    dict(
        cat = "Road Trip",
        en = "Do we need to stop for a rest?",
        gloss = ["Need to?", "stop", "for a while", "rest", "a bit"],
        yue = [("使唔使", "sai2 m4 sai2", [0]), ("停", "ting4", [1]), ("一陣", "jat1 zan6", [2]), ("休息", "jau1 sik1", [3]), ("吓", "haa5", [4])],
        cmn = [("要不要", "yào bu yào", [0]), ("停下来", "tíng xià lái", [1]), ("休息", "xiū xi", [3]), ("一下", "yí xià", [4])],
        tip = "\"X-not-X\" makes a yes/no question: 使唔使 sai2 m4 sai2 = need-not-need. Mandarin does the same with 要不要.",
    ),

    dict(
        cat = "Road Trip",
        en = "I'll drive, you can sleep.",
        gloss = ["I", "drive", "you", "can", "sleep"],
        yue = [("我", "ngo5", [0]), ("揸車", "zaa1 ce1", [1]), ("你", "nei5", [2]), ("可以", "ho2 ji5", [3]), ("瞓覺", "fan3 gaau3", [4])],
        cmn = [("我", "wǒ", [0]), ("开车", "kāi chē", [1]), ("你", "nǐ", [2]), ("可以", "kě yǐ", [3]), ("睡觉", "shuì jiào", [4])],
        tip = "Same word order in all three. Cantonese 揸車 is literally \"grip car\"; Mandarin 开车 is \"open car\".",
    ),

    dict(
        cat = "Road Trip",
        en = "Do you need to use the bathroom?",
        gloss = ["You", "need to?", "go to", "the bathroom", "(question tone)"],
        yue = [("你", "nei5", [0]), ("使唔使", "sai2 m4 sai2", [1]), ("去", "heoi3", [2]), ("洗手間", "sai2 sau2 gaan1", [3]), ("呀", "aa3", [4])],
        cmn = [("你", "nǐ", [0]), ("要不要", "yào bu yào", [1]), ("去", "qù", [2]), ("洗手间", "xǐ shǒu jiān", [3])],
        tip = "洗手間 is literally \"wash-hand room\", the polite word in both languages.",
    ),

    dict(
        cat = "Meals",
        en = "Have you eaten yet?",
        gloss = ["You", "have eaten", "(a meal)", "yet?"],
        yue = [("你", "nei5", [0]), ("食咗", "sik6 zo2", [1]), ("飯", "faan6", [2]), ("未呀", "mei6 aa3", [3])],
        cmn = [("你", "nǐ", [0]), ("吃饭", "chī fàn", [1, 2]), ("了吗", "le ma", [3])],
        tip = "A classic warm greeting, not just a food question. 咗 zo2 marks a finished action; 未 mei6 = \"not yet?\".",
    ),

    dict(
        cat = "Meals",
        en = "This is really delicious!",
        gloss = ["This", "(is) really", "delicious"],
        yue = [("呢個", "ni1 go3", [0]), ("好", "hou2", [1]), ("好食", "hou2 sik6", [2])],
        cmn = [("这个", "zhè ge", [0]), ("很", "hěn", [1]), ("好吃", "hǎo chī", [2])],
        tip = "好食 = good-eat. 好好味 hou2 hou2 mei6 (\"really tasty\") works too. Either one wins over the cook.",
    ),

    dict(
        cat = "Meals",
        en = "I'm full, thank you.",
        gloss = ["I", "(am) very", "full", "thank you"],
        yue = [("我", "ngo5", [0]), ("好", "hou2", [1]), ("飽", "baau2", [2]), ("多謝", "do1 ze6", [3])],
        cmn = [("我", "wǒ", [0]), ("很", "hěn", [1]), ("饱", "bǎo", [2]), ("谢谢", "xiè xie", [3])],
        tip = "Cantonese has two thank-yous: 多謝 do1 ze6 for gifts and meals, 唔該 m4 goi1 for small favours and service.",
    ),

    dict(
        cat = "Meals",
        en = "Please pass me the soy sauce.",
        gloss = ["Please", "pass", "to me", "the soy sauce"],
        yue = [("唔該", "m4 goi1", [0]), ("遞", "dai6", [1]), ("豉油", "si6 jau4", [3]), ("俾我", "bei2 ngo5", [2])],
        cmn = [("请", "qǐng", [0]), ("把", "bǎ", []), ("酱油", "jiàng yóu", [3]), ("递给", "dì gěi", [1, 2]), ("我", "wǒ", [2])],
        tip = "Mandarin 把 bǎ moves the object before the verb; it has no English word. Cantonese just says verb, object, then 俾我 \"to me\".",
    ),

    dict(
        cat = "Meals",
        en = "Everyone, let's eat!",
        gloss = ["Everyone", "let's", "eat"],
        yue = [("大家", "daai6 gaa1", [0]), ("食飯", "sik6 faan6", [2]), ("啦", "laa1", [1])],
        cmn = [("大家", "dà jiā", [0]), ("吃饭", "chī fàn", [2]), ("吧", "ba", [1])],
        tip = "\"Let's\" lives at the end of the sentence as a particle: 啦 laa1 / 吧 ba. Wait for elders to start eating first.",
    ),

    dict(
        cat = "Meals",
        en = "Would you like more tea?",
        gloss = ["Would you like?", "more", "tea"],
        yue = [("要唔要", "jiu3 m4 jiu3", [0]), ("添", "tim1", [1]), ("茶", "caa4", [2])],
        cmn = [("要不要", "yào bu yào", [0]), ("加", "jiā", [1]), ("茶", "chá", [2])],
        tip = "Pour for others before yourself. When someone refills your cup, tapping two fingers on the table says thanks.",
    ),

    dict(
        cat = "Weather",
        en = "It's so hot today.",
        gloss = ["(It's) so", "hot", "today"],
        yue = [("今日", "gam1 jat6", [2]), ("好", "hou2", [0]), ("熱", "jit6", [1])],
        cmn = [("今天", "jīn tiān", [2]), ("好", "hǎo", [0]), ("热", "rè", [1])],
        tip = "Time words go first in Chinese: \"today so hot\". No word for \"it's\" is needed.",
    ),

    dict(
        cat = "Weather",
        en = "Is it going to rain tomorrow?",
        gloss = ["Will it?", "rain", "tomorrow", "(question tone)"],
        yue = [("聽日", "ting1 jat6", [2]), ("會唔會", "wui5 m4 wui5", [0]), ("落雨", "lok6 jyu5", [1]), ("呀", "aa3", [3])],
        cmn = [("明天", "míng tiān", [2]), ("会不会", "huì bu huì", [0]), ("下雨", "xià yǔ", [1])],
        tip = "Rain \"falls\" in Cantonese (落 lok6) but \"comes down\" in Mandarin (下 xià). Tomorrow differs too: 聽日 vs 明天.",
    ),

    dict(
        cat = "Weather",
        en = "It's very cold outside.",
        gloss = ["(It's) very", "cold", "outside"],
        yue = [("出面", "ceot1 min6", [2]), ("好", "hou2", [0]), ("凍", "dung3", [1])],
        cmn = [("外面", "wài miàn", [2]), ("很", "hěn", [0]), ("冷", "lěng", [1])],
        tip = "Cantonese uses 凍 dung3 for cold weather; Mandarin uses 冷 lěng. 凍 in Mandarin mostly means \"frozen\".",
    ),

    dict(
        cat = "Weather",
        en = "Remember to bring a jacket.",
        gloss = ["Remember to", "bring", "a", "jacket"],
        yue = [("記得", "gei3 dak1", [0]), ("帶", "daai3", [1]), ("件", "gin6", [2]), ("褸", "lau1", [3])],
        cmn = [("记得", "jì de", [0]), ("带", "dài", [1]), ("件", "jiàn", [2]), ("外套", "wài tào", [3])],
        tip = "件 is a measure word for clothing, standing in for \"a\". Every noun has one; 個 go3 / 个 ge is the safe default.",
    ),

    dict(
        cat = "Weather",
        en = "The weather is really nice today.",
        gloss = ["The weather", "(is) really", "nice", "today"],
        yue = [("今日", "gam1 jat6", [3]), ("天氣", "tin1 hei3", [0]), ("好", "hou2", [1]), ("好", "hou2", [2])],
        cmn = [("今天", "jīn tiān", [3]), ("天气", "tiān qì", [0]), ("很", "hěn", [1]), ("好", "hǎo", [2])],
        tip = "In Cantonese the first 好 means \"very\" and the second means \"good\".",
    ),

    dict(
        cat = "Work",
        en = "How's work been lately?",
        gloss = ["How's", "work", "lately", "(question tone)"],
        yue = [("最近", "zeoi3 gan6", [2]), ("做嘢", "zou6 je5", [1]), ("點呀", "dim2 aa3", [0, 3])],
        cmn = [("最近", "zuì jìn", [2]), ("工作", "gōng zuò", [1]), ("怎么样", "zěn me yàng", [0])],
        tip = "做嘢 zou6 je5 is literally \"do stuff\", the everyday Cantonese verb for working.",
    ),

    dict(
        cat = "Work",
        en = "Are you busy at work?",
        gloss = ["You", "busy?", "at work"],
        yue = [("你", "nei5", [0]), ("做嘢", "zou6 je5", [2]), ("忙唔忙", "mong4 m4 mong4", [1]), ("呀", "aa3", [])],
        cmn = [("你", "nǐ", [0]), ("工作", "gōng zuò", [2]), ("忙不忙", "máng bu máng", [1])],
        tip = "Another busy-not-busy question. Topic first, then the question: \"you, work, busy-not-busy?\".",
    ),

    dict(
        cat = "Work",
        en = "What do you do for work?",
        gloss = ["What", "you", "do", "(for) work"],
        yue = [("你", "nei5", [1]), ("做", "zou6", [2]), ("咩嘢", "me1 je5", [0]), ("工", "gung1", [3]), ("㗎", "gaa3", [])],
        cmn = [("你", "nǐ", [1]), ("做", "zuò", [2]), ("什么", "shén me", [0]), ("工作", "gōng zuò", [3])],
        tip = "Question words stay where the answer would go: \"you do what work?\". No need to move \"what\" to the front.",
    ),

    dict(
        cat = "Work",
        en = "I work with computers.",
        gloss = ["I", "(am one who)", "works with", "computers", "(sentence end)"],
        yue = [("我", "ngo5", [0]), ("係", "hai6", [1]), ("做", "zou6", [2]), ("電腦", "din6 nou5", [3]), ("嘅", "ge3", [4])],
        cmn = [("我", "wǒ", [0]), ("是", "shì", [1]), ("做", "zuò", [2]), ("电脑", "diàn nǎo", [3]), ("的", "de", [4])],
        tip = "電腦 = \"electric brain\". The 係…嘅 / 是…的 frame describes what kind of person you are.",
    ),

    dict(
        cat = "Work",
        en = "Don't work yourself too hard!",
        gloss = ["Don't", "(be) too", "worn out", "(caring tone)"],
        yue = [("唔好", "m4 hou2", [0]), ("太", "taai3", [1]), ("辛苦", "san1 fu2", [2]), ("呀", "aa3", [3])],
        cmn = [("别", "bié", [0]), ("太", "tài", [1]), ("辛苦", "xīn kǔ", [2]), ("了", "le", [3])],
        tip = "辛苦晒 san1 fu2 saai3 (\"thanks for all your hard work\") is a great thing to say to whoever cooked or drove.",
    ),

    dict(
        cat = "Swimming",
        en = "Do you want to go swimming?",
        gloss = ["You", "want to?", "go", "swimming"],
        yue = [("你", "nei5", [0]), ("想唔想", "soeng2 m4 soeng2", [1]), ("去", "heoi3", [2]), ("游水", "jau4 seoi2", [3]), ("呀", "aa3", [])],
        cmn = [("你", "nǐ", [0]), ("想不想", "xiǎng bu xiǎng", [1]), ("去", "qù", [2]), ("游泳", "yóu yǒng", [3])],
        tip = "Cantonese 游水 = \"swim water\"; Mandarin 游泳 = \"swim swim\". 游泳 is understood in Cantonese too, but sounds formal.",
    ),

    dict(
        cat = "Swimming",
        en = "Is the water cold?",
        gloss = ["Is", "the", "water", "cold?"],
        yue = [("啲", "di1", [1]), ("水", "seoi2", [2]), ("凍唔凍", "dung3 m4 dung3", [0, 3]), ("呀", "aa3", [])],
        cmn = [("水", "shuǐ", [2]), ("冷不冷", "lěng bu lěng", [0, 3])],
        tip = "啲 di1 works like \"the\" for things you can't count. Mandarin can leave it out entirely.",
    ),

    dict(
        cat = "Swimming",
        en = "I forgot to bring my swimsuit.",
        gloss = ["I", "forgot", "to bring", "(my) swimsuit"],
        yue = [("我", "ngo5", [0]), ("唔記得", "m4 gei3 dak1", [1]), ("帶", "daai3", [2]), ("泳衣", "wing6 ji1", [3])],
        cmn = [("我", "wǒ", [0]), ("忘了", "wàng le", [1]), ("带", "dài", [2]), ("泳衣", "yǒng yī", [3])],
        tip = "Cantonese \"forget\" is 唔記得 = \"not remember\". Possessive \"my\" is usually dropped when it's obvious.",
    ),

    dict(
        cat = "Swimming",
        en = "Be careful, the water is deep.",
        gloss = ["Be careful", "the water", "(is) very", "deep"],
        yue = [("小心呀", "siu2 sam1 aa3", [0]), ("啲水", "di1 seoi2", [1]), ("好", "hou2", [2]), ("深", "sam1", [3])],
        cmn = [("小心", "xiǎo xīn", [0]), ("水", "shuǐ", [1]), ("很", "hěn", [2]), ("深", "shēn", [3])],
        tip = "小心 = \"small heart\". You'll hear 小心呀 constantly from aunties. It's affection.",
    ),

    dict(
        cat = "Helping Out",
        en = "Do you need anything?",
        gloss = ["You", "need?", "anything", "(question tone)"],
        yue = [("你", "nei5", [0]), ("要唔要", "jiu3 m4 jiu3", [1]), ("啲咩", "di1 me1", [2]), ("呀", "aa3", [3])],
        cmn = [("你", "nǐ", [0]), ("需要", "xū yào", [1]), ("什么", "shén me", [2]), ("吗", "ma", [3])],
        tip = "Mandarin turns statements into questions with 吗 ma. Cantonese prefers want-not-want plus a soft 呀.",
    ),

    dict(
        cat = "Helping Out",
        en = "Is there anything I can help with?",
        gloss = ["Is there", "anything", "(that) needs", "me", "to help"],
        yue = [("有冇", "jau5 mou5", [0]), ("嘢", "je5", [1]), ("要", "jiu3", [2]), ("我", "ngo5", [3]), ("幫手", "bong1 sau2", [4]), ("呀", "aa3", [])],
        cmn = [("有没有", "yǒu méi yǒu", [0]), ("什么", "shén me", [1]), ("需要", "xū yào", [2]), ("我", "wǒ", [3]), ("帮忙", "bāng máng", [4]), ("的", "de", [])],
        tip = "有冇 jau5 mou5 = have-not-have. 幫手 = \"help hand\". Offering this in the kitchen goes a long way.",
    ),

    dict(
        cat = "Helping Out",
        en = "Would you like some water?",
        gloss = ["You", "want to?", "drink", "some", "water"],
        yue = [("你", "nei5", [0]), ("要唔要", "jiu3 m4 jiu3", [1]), ("飲", "jam2", [2]), ("啲", "di1", [3]), ("水", "seoi2", [4]), ("呀", "aa3", [])],
        cmn = [("你", "nǐ", [0]), ("要不要", "yào bu yào", [1]), ("喝", "hē", [2]), ("点", "diǎn", [3]), ("水", "shuǐ", [4])],
        tip = "\"Drink\" is 飲 jam2 in Cantonese (as in 飲茶 yum cha) but 喝 hē in Mandarin.",
    ),

    dict(
        cat = "Helping Out",
        en = "Let me carry that for you.",
        gloss = ["Let", "me", "carry (it)", "for you"],
        yue = [("等", "dang2", [0]), ("我", "ngo5", [1]), ("幫你", "bong1 nei5", [3]), ("攞", "lo2", [2])],
        cmn = [("我", "wǒ", [1]), ("来", "lái", [0]), ("帮你", "bāng nǐ", [3]), ("拿", "ná", [2])],
        tip = "\"For you\" comes before the verb in both: \"let me help-you carry\". Note how Mandarin puts 我 before 来.",
    ),

    dict(
        cat = "Helping Out",
        en = "Thank you all for having me.",
        gloss = ["Thank", "you all", "for hosting", "me"],
        yue = [("多謝", "do1 ze6", [0]), ("你哋", "nei5 dei6", [1]), ("招呼", "ziu1 fu1", [2]), ("我", "ngo5", [3])],
        cmn = [("谢谢", "xiè xie", [0]), ("你们", "nǐ men", [1]), ("招待", "zhāo dài", [2]), ("我", "wǒ", [3])],
        tip = "你哋 nei5 dei6 / 你们 nǐ men make \"you\" plural. A perfect line for the end of the trip.",
    ),

]
