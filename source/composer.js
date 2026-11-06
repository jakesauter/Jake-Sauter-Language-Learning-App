  /* sentence composer: parses an English sentence into roles and rebuilds it in each language's own grammar */

  const Composer = (() => {

    const W = (y, yr, m, mr, t, tr, sure = true) => ({ yue: [y, yr], cmn: [m, mr], tsn: t ? [t, tr, sure] : null });

    /* checked function words and very common words, overriding the general dictionary */
    const CORE = {
      i: W("我", "ngo5", "我", "wǒ", "我", "ŋɔi33"),
      me: W("我", "ngo5", "我", "wǒ", "我", "ŋɔi33"),
      you: W("你", "nei5", "你", "nǐ", "你", "ni33"),
      he: W("佢", "keoi5", "他", "tā", "佢", "kui33"),
      him: W("佢", "keoi5", "他", "tā", "佢", "kui33"),
      she: W("佢", "keoi5", "她", "tā", "佢", "kui33"),
      her: W("佢", "keoi5", "她", "tā", "佢", "kui33"),
      it: W("佢", "keoi5", "它", "tā", "佢", "kui33"),
      we: W("我哋", "ngo5 dei6", "我们", "wǒ men", "我", "ŋɔi21", false),
      us: W("我哋", "ngo5 dei6", "我们", "wǒ men", "我", "ŋɔi21", false),
      they: W("佢哋", "keoi5 dei6", "他们", "tā men", "㑢", "kiak21"),
      them: W("佢哋", "keoi5 dei6", "他们", "tā men", "㑢", "kiak21"),
      "you all": W("你哋", "nei5 dei6", "你们", "nǐ men", "你", "ni21", false),
      everyone: W("大家", "daai6 gaa1", "大家", "dà jiā", "仲家", "jəŋ32 ga215"),
      go: W("去", "heoi3", "去", "qù", "去", "hui33"),
      come: W("嚟", "lai4", "来", "lái", "來", "lɔi22"),
      eat: W("食", "sik6", "吃", "chī", "吃", "hiak33"),
      drink: W("飲", "jam2", "喝", "hē", "飲", "ŋim55"),
      want: W("想", "soeng2", "想", "xiǎng", "想", "ɬiaŋ55", false),
      like: W("鍾意", "zung1 ji3", "喜欢", "xǐ huan", "中意", "dzəŋ33 yi33"),
      love: W("好鍾意", "hou2 zung1 ji3", "爱", "ài", "好中意", "hɔu55 dzəŋ33 yi33"),
      see: W("見", "gin3", "看见", "kàn jiàn", "見", "gein33"),
      watch: W("睇", "tai2", "看", "kàn", "睇", "hai55"),
      look: W("睇", "tai2", "看", "kàn", "睇", "hai55"),
      play: W("玩", "waan2", "玩", "wán", "玩", "van22", false),
      sleep: W("瞓覺", "fan3 gaau3", "睡觉", "shuì jiào", "瞓覺", "fun33 gɔu33"),
      buy: W("買", "maai5", "买", "mǎi", "買", "mai33"),
      cook: W("煮飯", "zyu2 faan6", "做饭", "zuò fàn", "煮飯", "dzi55 fan32"),
      make: W("整", "zing2", "做", "zuò", "整", "dzein55"),
      do: W("做", "zou6", "做", "zuò", "做", "du33"),
      call: W("打電話畀", "daa2 din6 waa2 bei2", "打电话给", "dǎ diàn huà gěi", "打電話畀", "a55 ein32 va325 i55"),
      visit: W("探", "taam3", "看望", "kàn wàng", "探", "ham33", false),
      help: W("幫", "bong1", "帮", "bāng", "幫", "bɔŋ33"),
      home: W("屋企", "uk1 kei2", "家", "jiā", "屋企", "ək55 ki55"),
      mom: W("媽咪", "maa1 mi4", "妈妈", "mā ma", "阿媽", "a33 ma55", false),
      dad: W("爹哋", "de1 di4", "爸爸", "bà ba", "阿爸", "a33 ba55", false),
      grandma: W("婆婆", "po4 po2", "奶奶", "nǎi nai", "阿人", "a33 ŋin22"),
      grandpa: W("公公", "gung4 gung1", "爷爷", "yé ye", "阿公", "a33 gəŋ33", false),
      dinner: W("晚飯", "maan5 faan6", "晚饭", "wǎn fàn", "晚飯", "man21 fan32", false),
      lunch: W("晏晝", "aan3 zau3", "午饭", "wǔ fàn", "晏晝", "an33 tsiu215"),
      breakfast: W("早餐", "zou2 caan1", "早饭", "zǎo fàn", "早餐", "dɔu55 tan335"),
      food: W("嘢食", "je5 sik6", "东西", "dōng xi", "嘢吃", "yia33 hiak33"),
      weekend: W("週末", "zau1 mut6", "周末", "zhōu mò", "禮拜六日", "lai21 bai33 lək32 ŋit21", false),
      today: W("今日", "gam1 jat6", "今天", "jīn tiān", "今日", "gim33 ŋit21"),
      tonight: W("今晚", "gam1 maan5", "今晚", "jīn wǎn", "今晚", "gim33 man21"),
      tomorrow: W("聽日", "ting1 jat6", "明天", "míng tiān", "天早", "hein32 dɔu55"),
      yesterday: W("琴日", "kam4 jat6", "昨天", "zuó tiān", "琴日", "kim22 ŋit21", false),
      now: W("而家", "ji4 gaa1", "现在", "xiàn zài", "而家", "yi22 ga33", false),
      later: W("遲啲", "ci4 di1", "等一下", "děng yí xià", "遲啲", "tsi22 nit55", false),
      store: W("超市", "ciu1 si5", "超市", "chāo shì", "士多舖", "si21 dɔ55 pu335"),
      what: W("乜嘢", "mat1 je5", "什么", "shén me", "乜嘢", "mɔt55 yia33"),
      who: W("邊個", "bin1 go3", "谁", "shéi", "谁", "sui55"),
      where: W("邊度", "bin1 dou6", "哪里", "nǎ li", "哪", "nai215"),
      when: W("幾時", "gei2 si4", "什么时候", "shén me shí hou", "幾時", "gi55 si215"),
      how: W("點樣", "dim2 joeng2", "怎么", "zěn me", "點", "iam55"),
      why: W("點解", "dim2 gaai2", "为什么", "wèi shén me", "做乜", "du33 mɔt55", false),
      tired: W("攰", "gui6", "累", "lèi", "攰", "gui32", false),
      hungry: W("肚餓", "tou5 ngo6", "饿", "è", "肚飢", "u55 gi33", false),
      cantonese: W("廣東話", "gwong2 dung1 waa2", "粤语", "yuè yǔ", "廣東話", "gɔŋ55 əŋ33 va325", false),
      mandarin: W("普通話", "pou2 tung1 waa2", "普通话", "pǔ tōng huà", "國語", "kɔk33 ŋi21", false),
      taishanese: W("台山話", "toi4 saan1 waa2", "台山话", "tái shān huà", "台山話", "hɔi22 san33 va325"),
      english: W("英文", "jing1 man2", "英语", "yīng yǔ", "英文", "yein33 mun22", false),
      chinese: W("中文", "zung1 man2", "中文", "zhōng wén", "唐話", "hɔŋ22 va325", false),
      key: W("鎖匙", "so2 si4", "钥匙", "yào shi", "鎖匙", "ɬɔ55 si22"),
      find: W("搵到", "wan2 dou2", "找到", "zhǎo dào", "搵到", "vun55 ɔu55"),
      sit: W("坐低", "co5 dai1", "坐下", "zuò xià", "坐", "tɔ33"),
      bathroom: W("廁所", "ci3 so2", "洗手间", "xǐ shǒu jiān", "廁所", "tsi33 sɔ55", false),
      toilet: W("廁所", "ci3 so2", "厕所", "cè suǒ", "廁所", "tsi33 sɔ55", false),
      "go out": W("出去", "ceot1 heoi3", "出去", "chū qù", "出去", "tsut55 hui33"),
      "help n": W("幫手", "bong1 sau2", "帮助", "bāng zhù", "幫手", "bɔŋ33 siu55", false),
      something: W("嘢", "je5", "东西", "dōng xi", "嘢", "yia33"),
      anything: W("任何嘢", "jam6 ho4 je5", "任何东西", "rèn hé dōng xi", "乜嘢", "mɔt55 yia33", false),
      it: W("佢", "keoi5", "它", "tā", "佢", "kui33"),
      need: W("需要", "seoi1 jiu3", "需要", "xū yào", "需要", "ɬui33 yiau33", false),
      milk: W("牛奶", "ngau4 naai5", "牛奶", "niú nǎi", "牛奶", "ŋəu22 nai21"),
      friend: W("朋友", "pang4 jau5", "朋友", "péng you", "朋友", "paŋ22 yiu21"),
      phone: W("電話", "din6 waa2", "手机", "shǒu jī", "手機", "siu55 gi33"),
      together: W("一齊", "jat1 cai4", "一起", "yì qǐ", "一齊", "yit55 tai225"),
      also: W("都", "dou1", "也", "yě", "都", "u33", false),
      too: W("都", "dou1", "也", "yě", "都", "u33", false),
      very: W("好", "hou2", "很", "hěn", "好", "hɔu55"),
      so: W("好", "hou2", "好", "hǎo", "好", "hɔu55"),
      really: W("真係", "zan1 hai6", "真的", "zhēn de", "真係", "tsin33 hai32", false),
      "a lot": W("好多", "hou2 do1", "很多", "hěn duō", "好多", "hɔu55 ɔ33", false),
      "a little": W("少少", "siu2 siu2", "一点", "yì diǎn", "啲", "nit55", false),
      again: W("再", "zoi3", "再", "zài", "再", "dɔi33", false),
      already: W("已經", "ji5 ging1", "已经", "yǐ jīng", "已經", "yi21 gein33", false),
      here: W("呢度", "ni1 dou6", "这里", "zhè li", "該埞", "kɔi21 tiaŋ215"),
      there: W("嗰度", "go2 dou6", "那里", "nà li", "許埞", "hui55 tiaŋ215", false),
    };

    const FN = {
      not: W("唔", "m4", "不", "bù", "唔", "m22"),
      notPast: W("冇", "mou5", "没", "méi", "冇", "mɔu33"),
      notWill: W("唔會", "m4 wui5", "不会", "bú huì", "唔會", "m22 vui32", false),
      past: W("咗", "zo2", "了", "le", "啊", "ə33"),
      yet: W("未", "mei6", "了吗", "le ma", "唔曾", "miaŋ21"),
      haveNot: W("有冇", "jau5 mou5", "有没有", "yǒu méi yǒu", "有冇", "yiu33 mɔu55"),
      q: W("呀", "aa3", "吗", "ma", "啊", "a33"),
      qWh: W("呀", "aa3", "", "", "啊", "a33"),
      lets: W("啦", "laa1", "吧", "ba", "啦", "la55"),
      please: W("唔該", "m4 goi1", "请", "qǐng", "唔該", "m22 gɔi33"),
      want: W("想", "soeng2", "想", "xiǎng", "想", "ɬiaŋ55", false),
      can: W("可以", "ho2 ji5", "可以", "kě yǐ", "可以", "hɔ55 yi21"),
      know: W("識", "sik1", "会", "huì", "識", "sɛt55"),
      need: W("要", "jiu3", "要", "yào", "要", "yiau33", false),
      should: W("應該", "jing1 goi1", "应该", "yīng gāi", "應該", "yein33 gɔi33", false),
      will: W("會", "wui5", "会", "huì", "會", "vui32", false),
      like: W("鍾意", "zung1 ji3", "喜欢", "xǐ huan", "中意", "dzəŋ33 yi33"),
      with: W("同", "tung4", "跟", "gēn", "同", "həŋ22"),
      at: W("喺", "hai2", "在", "zài", "喺", "hai55", false),
      for: W("幫", "bong1", "给", "gěi", "幫", "bɔŋ33"),
      very: W("好", "hou2", "很", "hěn", "好", "hɔu55"),
      too: W("太", "taai3", "太", "tài", "太", "hai33", false),
      have: W("有", "jau5", "有", "yǒu", "有", "yiu33"),
      be: W("係", "hai6", "是", "shì", "係", "hai32"),
      of: W("嘅", "ge3", "的", "de", "個", "gɔi33", false),
      this: W("呢個", "ni1 go3", "这个", "zhè ge", "該個", "kɔi21 gɔi33", false),
      that: W("嗰個", "go2 go3", "那个", "nà ge", "許個", "hui55 gɔi33", false),
      more: W("多啲", "do1 di1", "多一点", "duō yì diǎn", "多啲", "ɔ33 nit55", false),
      some: W("啲", "di1", "一些", "yì xiē", "啲", "nit55", false),
      howMuch: W("幾多錢", "gei2 do1 cin2", "多少钱", "duō shao qián", "幾多錢", "gi55 ɔ335 tein225", false),
      howMany: W("幾多", "gei2 do1", "多少", "duō shao", "幾多", "gi55 ɔ335", false),
      go: W("去", "heoi3", "去", "qù", "去", "hui33"),
      togetherV: W("一齊", "jat1 cai4", "一起", "yì qǐ", "一齊", "yit55 tai225"),
    };

    const MEALS = { breakfast: ["desayunar", "prendre le petit-déjeuner", "frühstücken"], lunch: ["comer", "déjeuner", "zu Mittag essen"], dinner: ["cenar", "dîner", "zu Abend essen"] };
    const DE_PL = { Freund: "Freunden", Freundin: "Freundinnen", Kind: "Kindern", Cousin: "Cousins", Bruder: "Brüdern", Schwester: "Schwestern", Eltern: "Eltern" };
    const LANGS = new Set("cantonese mandarin taishanese english chinese spanish french german".split(" "));
    const KIN = new Set("mom dad mother father grandma grandpa grandmother grandfather brother sister uncle aunt son daughter husband wife girlfriend boyfriend family parents cousin kids children friend".split(" "));
    const SKILL = new Set("swim drive cook speak read write dance sing ride".split(" "));
    const MOTION = new Set("go come return walk run drive leave travel".split(" "));

    const TIME = ["this weekend", "next week", "last week", "next month", "this morning", "this afternoon", "this evening", "tomorrow morning", "tomorrow night", "last night", "every day", "every morning", "every night", "on the weekend", "right now", "today", "tonight", "tomorrow", "yesterday", "now", "later", "soon", "sometimes", "always", "often", "never", "already", "again", "on sunday", "on saturday", "on monday", "on friday"];

    const TIME_X = {
      "this weekend": [["今個週末", "gam1 go3 zau1 mut6"], ["这个周末", "zhè ge zhōu mò"], ["今個禮拜六日", "gim33 gɔi33 lai21 bai33 lək32 ŋit21", false], "este fin de semana", "ce week-end", "am Wochenende"],
      "next week": [["下個禮拜", "haa6 go3 lai5 baai3"], ["下周", "xià zhōu"], ["下個禮拜", "ha32 gɔi33 lai21 bai33", false], "la próxima semana", "la semaine prochaine", "nächste Woche"],
      "last week": [["上個禮拜", "soeng6 go3 lai5 baai3"], ["上周", "shàng zhōu"], ["上個禮拜", "siaŋ32 gɔi33 lai21 bai33", false], "la semana pasada", "la semaine dernière", "letzte Woche"],
      "next month": [["下個月", "haa6 go3 jyut6"], ["下个月", "xià ge yuè"], ["下個月", "ha32 gɔi33 ŋut32", false], "el próximo mes", "le mois prochain", "nächsten Monat"],
      "this morning": [["今朝", "gam1 ziu1"], ["今天早上", "jīn tiān zǎo shang"], ["今朝", "gim33 tsiu33", false], "esta mañana", "ce matin", "heute Morgen"],
      "this afternoon": [["今日下晝", "gam1 jat6 haa6 zau3"], ["今天下午", "jīn tiān xià wǔ"], ["今日下晝", "gim33 ŋit21 ha32 tsiu33", false], "esta tarde", "cet après-midi", "heute Nachmittag"],
      "this evening": [["今晚", "gam1 maan5"], ["今晚", "jīn wǎn"], ["今晚", "gim33 man21"], "esta noche", "ce soir", "heute Abend"],
      "tomorrow morning": [["聽朝", "ting1 ziu1"], ["明天早上", "míng tiān zǎo shang"], ["天早朝", "hein32 dɔu55 tsiu33", false], "mañana en la mañana", "demain matin", "morgen früh"],
      "tomorrow night": [["聽晚", "ting1 maan5"], ["明天晚上", "míng tiān wǎn shang"], ["天早晚", "hein32 dɔu55 man21", false], "mañana en la noche", "demain soir", "morgen Abend"],
      "last night": [["琴晚", "kam4 maan5"], ["昨晚", "zuó wǎn"], ["琴晚", "kim22 man21", false], "anoche", "hier soir", "gestern Abend"],
      "every day": [["日日", "jat6 jat6"], ["每天", "měi tiān"], ["日日", "ŋit21 ŋit21", false], "todos los días", "tous les jours", "jeden Tag"],
      "every morning": [["朝朝", "ziu1 ziu1"], ["每天早上", "měi tiān zǎo shang"], ["朝朝", "tsiu33 tsiu33", false], "todas las mañanas", "tous les matins", "jeden Morgen"],
      "every night": [["晚晚", "maan5 maan5"], ["每天晚上", "měi tiān wǎn shang"], ["晚晚", "man21 man21", false], "todas las noches", "tous les soirs", "jeden Abend"],
      "on the weekend": [["週末", "zau1 mut6"], ["周末", "zhōu mò"], ["禮拜六日", "lai21 bai33 lək32 ŋit21", false], "el fin de semana", "le week-end", "am Wochenende"],
      "right now": [["而家", "ji4 gaa1"], ["现在", "xiàn zài"], ["而家", "yi22 ga33", false], "ahora mismo", "tout de suite", "jetzt gleich"],
      today: [["今日", "gam1 jat6"], ["今天", "jīn tiān"], ["今日", "gim33 ŋit21"], "hoy", "aujourd'hui", "heute"],
      tonight: [["今晚", "gam1 maan5"], ["今晚", "jīn wǎn"], ["今晚", "gim33 man21"], "esta noche", "ce soir", "heute Abend"],
      tomorrow: [["聽日", "ting1 jat6"], ["明天", "míng tiān"], ["天早", "hein32 dɔu55"], "mañana", "demain", "morgen"],
      yesterday: [["琴日", "kam4 jat6"], ["昨天", "zuó tiān"], ["琴日", "kim22 ŋit21", false], "ayer", "hier", "gestern"],
      now: [["而家", "ji4 gaa1"], ["现在", "xiàn zài"], ["而家", "yi22 ga33", false], "ahora", "maintenant", "jetzt"],
      later: [["遲啲", "ci4 di1"], ["等一下", "děng yí xià"], ["遲啲", "tsi22 nit55", false], "más tarde", "plus tard", "später"],
      soon: [["就快", "zau6 faai3"], ["马上", "mǎ shàng"], ["就快", "diu32 fai33", false], "pronto", "bientôt", "bald"],
      sometimes: [["有時", "jau5 si4"], ["有时候", "yǒu shí hou"], ["有時", "yiu33 si22", false], "a veces", "parfois", "manchmal"],
      always: [["成日", "seng4 jat6"], ["总是", "zǒng shì"], ["成日", "siaŋ22 ŋi215"], "siempre", "toujours", "immer"],
      often: [["成日", "seng4 jat6"], ["经常", "jīng cháng"], ["成日", "siaŋ22 ŋi215"], "seguido", "souvent", "oft"],
      never: [["從來都唔", "cung4 loi4 dou1 m4"], ["从来不", "cóng lái bù"], ["從來唔", "tsəŋ22 lɔi22 m22", false], "nunca", "jamais", "nie"],
      already: [["已經", "ji5 ging1"], ["已经", "yǐ jīng"], ["已經", "yi21 gein33", false], "ya", "déjà", "schon"],
      again: [["再", "zoi3"], ["再", "zài"], ["再", "dɔi33", false], "otra vez", "encore", "wieder"],
      "on sunday": [["星期日", "sing1 kei4 jat6"], ["周日", "zhōu rì"], ["禮拜日", "lai21 bai33 ŋit215"], "el domingo", "dimanche", "am Sonntag"],
      "on saturday": [["星期六", "sing1 kei4 luk6"], ["周六", "zhōu liù"], ["禮拜六", "lai21 bai33 lək32", false], "el sábado", "samedi", "am Samstag"],
      "on monday": [["星期一", "sing1 kei4 jat1"], ["周一", "zhōu yī"], ["禮拜一", "lai21 bai33 yit55", false], "el lunes", "lundi", "am Montag"],
      "on friday": [["星期五", "sing1 kei4 ng5"], ["周五", "zhōu wǔ"], ["禮拜五", "lai21 bai33 ŋ21", false], "el viernes", "vendredi", "am Freitag"],
    };

    const ADJ = new Set("good bad big small little hot cold warm cool beautiful pretty delicious tasty happy sad angry tired hungry thirsty full sick busy free fast slow early late cheap expensive new old same different easy difficult hard right wrong okay ok fun funny interesting boring cute handsome smart lucky safe ready dirty clean nice kind great amazing terrible excited nervous bored scared proud sleepy worried surprised healthy strong weak tall short young quiet loud spicy sweet salty sour fresh far near close sorry sure lost married".split(" "));
    const STATE = new Set("tired hungry thirsty full sick busy free ready happy sad angry excited nervous bored scared proud sleepy worried surprised lost late okay ok sure sorry married dirty clean".split(" "));
    const WEATHER = { hot: ["calor", "chaud", "heiß"], cold: ["frío", "froid", "kalt"], warm: ["calor", "doux", "warm"], cool: ["fresco", "frais", "kühl"], sunny: ["sol", "beau", "sonnig"], windy: ["viento", "du vent", "windig"] };

    const PAST_EN = { went: "go", ate: "eat", drank: "drink", saw: "see", came: "come", gave: "give", took: "take", said: "say", made: "make", got: "get", knew: "know", thought: "think", bought: "buy", slept: "sleep", ran: "run", sat: "sit", told: "tell", felt: "feel", left: "leave", brought: "bring", taught: "teach", met: "meet", paid: "pay", spoke: "speak", wrote: "write", swam: "swim", drove: "drive", forgot: "forget", began: "begin", found: "find", had: "have", did: "do", was: "be", were: "be", cooked: "cook", called: "call", watched: "watch", played: "play", visited: "visit", worked: "work", finished: "finish", cleaned: "clean", talked: "talk", walked: "walk", wanted: "want", liked: "like", loved: "love", missed: "miss", helped: "help", tried: "try", studied: "study", arrived: "arrive", stayed: "stay", washed: "wash", learned: "learn", lived: "live", opened: "open", closed: "close", needed: "need", listened: "listen", danced: "dance", rested: "rest", started: "start" };


    /* ---------- Spanish ---------- */

    const ES_PRON = ["yo", "tú", "él", "ella", "nosotros", "ustedes", "ellos"];
    const ES_IRR = {
      ser: ["soy", "eres", "es", "somos", "son"], estar: ["estoy", "estás", "está", "estamos", "están"], ir: ["voy", "vas", "va", "vamos", "van"],
      tener: ["tengo", "tienes", "tiene", "tenemos", "tienen"], venir: ["vengo", "vienes", "viene", "venimos", "vienen"], hacer: ["hago", "haces", "hace", "hacemos", "hacen"],
      decir: ["digo", "dices", "dice", "decimos", "dicen"], poner: ["pongo", "pones", "pone", "ponemos", "ponen"], salir: ["salgo", "sales", "sale", "salimos", "salen"],
      saber: ["sé", "sabes", "sabe", "sabemos", "saben"], ver: ["veo", "ves", "ve", "vemos", "ven"], dar: ["doy", "das", "da", "damos", "dan"], traer: ["traigo", "traes", "trae", "traemos", "traen"],
      conocer: ["conozco", "conoces", "conoce", "conocemos", "conocen"], querer: ["quiero", "quieres", "quiere", "queremos", "quieren"], poder: ["puedo", "puedes", "puede", "podemos", "pueden"],
      dormir: ["duermo", "duermes", "duerme", "dormimos", "duermen"], jugar: ["juego", "juegas", "juega", "jugamos", "juegan"], pensar: ["pienso", "piensas", "piensa", "pensamos", "piensan"],
      volver: ["vuelvo", "vuelves", "vuelve", "volvemos", "vuelven"], empezar: ["empiezo", "empiezas", "empieza", "empezamos", "empiezan"], entender: ["entiendo", "entiendes", "entiende", "entendemos", "entienden"],
      sentir: ["siento", "sientes", "siente", "sentimos", "sienten"], preferir: ["prefiero", "prefieres", "prefiere", "preferimos", "prefieren"], oír: ["oigo", "oyes", "oye", "oímos", "oyen"],
      probar: ["pruebo", "pruebas", "prueba", "probamos", "prueban"], encontrar: ["encuentro", "encuentras", "encuentra", "encontramos", "encuentran"], recordar: ["recuerdo", "recuerdas", "recuerda", "recordamos", "recuerdan"],
      acordar: ["acuerdo", "acuerdas", "acuerda", "acordamos", "acuerdan"], despertar: ["despierto", "despiertas", "despierta", "despertamos", "despiertan"], sentar: ["siento", "sientas", "sienta", "sentamos", "sientan"],
      llover: ["llueve", "llueve", "llueve", "llueve", "llueve"], costar: ["cuesta", "cuesta", "cuesta", "cuestan", "cuestan"], pedir: ["pido", "pides", "pide", "pedimos", "piden"], servir: ["sirvo", "sirves", "sirve", "servimos", "sirven"], seguir: ["sigo", "sigues", "sigue", "seguimos", "siguen"], perder: ["pierdo", "pierdes", "pierde", "perdemos", "pierden"], cerrar: ["cierro", "cierras", "cierra", "cerramos", "cierran"], mover: ["muevo", "mueves", "mueve", "movemos", "mueven"], doler: ["duele", "duele", "duele", "duelen", "duelen"], reír: ["río", "ríes", "ríe", "reímos", "ríen"], sonreír: ["sonrío", "sonríes", "sonríe", "sonreímos", "sonríen"], morir: ["muero", "mueres", "muere", "morimos", "mueren"], crecer: ["crezco", "creces", "crece", "crecemos", "crecen"],
    };
    const ES_PRET = {
      ser: ["fui", "fuiste", "fue", "fuimos", "fueron"], ir: ["fui", "fuiste", "fue", "fuimos", "fueron"], estar: ["estuve", "estuviste", "estuvo", "estuvimos", "estuvieron"], tener: ["tuve", "tuviste", "tuvo", "tuvimos", "tuvieron"],
      hacer: ["hice", "hiciste", "hizo", "hicimos", "hicieron"], poder: ["pude", "pudiste", "pudo", "pudimos", "pudieron"], decir: ["dije", "dijiste", "dijo", "dijimos", "dijeron"], venir: ["vine", "viniste", "vino", "vinimos", "vinieron"],
      traer: ["traje", "trajiste", "trajo", "trajimos", "trajeron"], ver: ["vi", "viste", "vio", "vimos", "vieron"], dar: ["di", "diste", "dio", "dimos", "dieron"], querer: ["quise", "quisiste", "quiso", "quisimos", "quisieron"],
      saber: ["supe", "supiste", "supo", "supimos", "supieron"], poner: ["puse", "pusiste", "puso", "pusimos", "pusieron"], dormir: ["dormí", "dormiste", "durmió", "dormimos", "durmieron"], leer: ["leí", "leíste", "leyó", "leímos", "leyeron"],
      oír: ["oí", "oíste", "oyó", "oímos", "oyeron"], pedir: ["pedí", "pediste", "pidió", "pedimos", "pidieron"], sentir: ["sentí", "sentiste", "sintió", "sentimos", "sintieron"], conducir: ["conduje", "condujiste", "condujo", "condujimos", "condujeron"],
    };
    const ES_IMP = { ir: "ve", venir: "ven", hacer: "haz", decir: "di", poner: "pon", salir: "sal", tener: "ten", ser: "sé" };
    const ES_SUBJ_YO = { ir: "vay", ser: "se", estar: "est", saber: "sep", dar: "d", ver: "ve" };

    function esPresent(inf, p) {
      if (ES_IRR[inf]) return ES_IRR[inf][p];
      const end = inf.slice(-2), st = inf.slice(0, -2);
      const T = { ar: ["o", "as", "a", "amos", "an"], er: ["o", "es", "e", "emos", "en"], ir: ["o", "es", "e", "imos", "en"], "ír": ["o", "es", "e", "imos", "en"] }[end];
      return T ? st + T[p] : inf;
    }

    function esPret(inf, p) {
      if (ES_PRET[inf]) return ES_PRET[inf][p];
      const end = inf.slice(-2);
      let st = inf.slice(0, -2);
      if (end === "ar") {
        if (p === 0) st = st.replace(/c$/, "qu").replace(/g$/, "gu").replace(/z$/, "c");
        return st + ["é", "aste", "ó", "amos", "aron"][p];
      }
      return st + ["í", "iste", "ió", "imos", "ieron"][p];
    }

    function esAccent(w) {
      if (/[áéíóú]/.test(w)) return w;
      const groups = [...w.matchAll(/[aeiou]+/g)];
      if (groups.length < 2) return w;
      if (!/[aeiou]$/.test(w)) return w;
      const gg = groups[groups.length - 2];
      const strong = gg[0].search(/[aeo]/) >= 0 ? gg.index + gg[0].search(/[aeo]/) : gg.index + gg[0].length - 1;
      const map = { a: "á", e: "é", i: "í", o: "ó", u: "ú" };
      return w.slice(0, strong) + map[w[strong]] + w.slice(strong + 1);
    }

    function esImperative(inf) {
      if (ES_IMP[inf]) return ES_IMP[inf];
      return esPresent(inf, 2);
    }

    function esSubj(inf, p) {
      const yo = ES_SUBJ_YO[inf] !== undefined ? ES_SUBJ_YO[inf] + "o" : esPresent(inf, 0);
      const st = yo.replace(/o$/, "");
      const ar = inf.endsWith("ar") && !ES_SUBJ_YO[inf];
      const T = ar ? ["e", "es", "e", "emos", "en"] : ["a", "as", "a", "amos", "an"];
      return st + T[p];
    }

    const esRefl = ["me", "te", "se", "nos", "se"];
    const esIO = ["me", "te", "le", "nos", "les"];


    /* ---------- French ---------- */

    const FR_IRR = {
      "être": ["suis", "es", "est", "est", "êtes", "sont"], avoir: ["ai", "as", "a", "a", "avez", "ont"], aller: ["vais", "vas", "va", "va", "allez", "vont"], faire: ["fais", "fais", "fait", "fait", "faites", "font"],
      vouloir: ["veux", "veux", "veut", "veut", "voulez", "veulent"], pouvoir: ["peux", "peux", "peut", "peut", "pouvez", "peuvent"], devoir: ["dois", "dois", "doit", "doit", "devez", "doivent"], prendre: ["prends", "prends", "prend", "prend", "prenez", "prennent"],
      apprendre: ["apprends", "apprends", "apprend", "apprend", "apprenez", "apprennent"], comprendre: ["comprends", "comprends", "comprend", "comprend", "comprenez", "comprennent"], venir: ["viens", "viens", "vient", "vient", "venez", "viennent"], revenir: ["reviens", "reviens", "revient", "revient", "revenez", "reviennent"],
      voir: ["vois", "vois", "voit", "voit", "voyez", "voient"], savoir: ["sais", "sais", "sait", "sait", "savez", "savent"], dire: ["dis", "dis", "dit", "dit", "dites", "disent"], boire: ["bois", "bois", "boit", "boit", "buvez", "boivent"],
      dormir: ["dors", "dors", "dort", "dort", "dormez", "dorment"], partir: ["pars", "pars", "part", "part", "partez", "partent"], sortir: ["sors", "sors", "sort", "sort", "sortez", "sortent"], lire: ["lis", "lis", "lit", "lit", "lisez", "lisent"],
      "écrire": ["écris", "écris", "écrit", "écrit", "écrivez", "écrivent"], mettre: ["mets", "mets", "met", "met", "mettez", "mettent"], conduire: ["conduis", "conduis", "conduit", "conduit", "conduisez", "conduisent"], courir: ["cours", "cours", "court", "court", "courez", "courent"],
      ouvrir: ["ouvre", "ouvres", "ouvre", "ouvre", "ouvrez", "ouvrent"], connaître: ["connais", "connais", "connaît", "connaît", "connaissez", "connaissent"], croire: ["crois", "crois", "croit", "croit", "croyez", "croient"], vivre: ["vis", "vis", "vit", "vit", "vivez", "vivent"],
      sentir: ["sens", "sens", "sent", "sent", "sentez", "sentent"], acheter: ["achète", "achètes", "achète", "achète", "achetez", "achètent"], appeler: ["appelle", "appelles", "appelle", "appelle", "appelez", "appellent"], "préférer": ["préfère", "préfères", "préfère", "préfère", "préférez", "préfèrent"],
      "s'asseoir": ["assieds", "assieds", "assied", "assied", "asseyez", "asseyent"], recevoir: ["reçois", "reçois", "reçoit", "reçoit", "recevez", "reçoivent"], rire: ["ris", "ris", "rit", "rit", "riez", "rient"], sourire: ["souris", "souris", "sourit", "sourit", "souriez", "sourient"], pleuvoir: ["pleut", "pleut", "pleut", "pleut", "pleut", "pleut"], "se souvenir": ["souviens", "souviens", "souvient", "souvient", "souvenez", "souviennent"],
    };
    const FR_PP = { "être": "été", avoir: "eu", aller: "allé", faire: "fait", vouloir: "voulu", pouvoir: "pu", devoir: "dû", prendre: "pris", apprendre: "appris", comprendre: "compris", venir: "venu", revenir: "revenu", voir: "vu", savoir: "su", dire: "dit", boire: "bu", dormir: "dormi", partir: "parti", sortir: "sorti", lire: "lu", "écrire": "écrit", mettre: "mis", conduire: "conduit", courir: "couru", ouvrir: "ouvert", connaître: "connu", croire: "cru", vivre: "vécu", sentir: "senti", recevoir: "reçu", rire: "ri", sourire: "souri", "s'asseoir": "assis", naître: "né", mourir: "mort", pleuvoir: "plu" };
    const FR_ETRE = new Set(["aller", "venir", "revenir", "partir", "sortir", "arriver", "rester", "rentrer", "naître", "mourir", "tomber", "monter", "descendre", "retourner", "devenir"]);
    const FR_NOUS = { aller: "allons", faire: "faisons", prendre: "prenons", venir: "venons", boire: "buvons", voir: "voyons", dire: "disons", partir: "partons", sortir: "sortons", lire: "lisons", "écrire": "écrivons", mettre: "mettons", "être": "soyons", avoir: "ayons", manger: "mangeons", nager: "nageons", commencer: "commençons", dormir: "dormons", courir: "courons", conduire: "conduisons", attendre: "attendons", finir: "finissons" };

    function frPresent(inf, p) {
      if (FR_IRR[inf]) return FR_IRR[inf][p];
      if (inf.endsWith("er")) {
        const st = inf.slice(0, -2);
        return st + ["e", "es", "e", "e", "ez", "ent"][p];
      }
      if (inf.endsWith("ir")) {
        const st = inf.slice(0, -2);
        return st + ["is", "is", "it", "it", "issez", "issent"][p];
      }
      if (inf.endsWith("re")) {
        const st = inf.slice(0, -2);
        return st + ["s", "s", "", "", "ez", "ent"][p];
      }
      return inf;
    }

    function frPP(inf) {
      if (FR_PP[inf]) return FR_PP[inf];
      if (inf.endsWith("er")) return inf.slice(0, -2) + "é";
      if (inf.endsWith("ir")) return inf.slice(0, -2) + "i";
      if (inf.endsWith("re")) return inf.slice(0, -2) + "u";
      return inf;
    }

    function frImperative(inf) {
      if (inf === "aller") return "va";
      if (inf === "être") return "sois";
      if (inf === "avoir") return "aie";
      const tu = frPresent(inf, 1);
      return inf.endsWith("er") || inf === "ouvrir" ? tu.replace(/s$/, "") : tu;
    }

    function frNous(inf) {
      if (FR_NOUS[inf]) return FR_NOUS[inf];
      if (inf.endsWith("er")) return inf.slice(0, -2) + "ons";
      if (inf.endsWith("ir")) return inf.slice(0, -2) + "issons";
      if (inf.endsWith("re")) return inf.slice(0, -2) + "ons";
      return inf;
    }

    const elide = w => /^[aeiouéèêhâîôûœ]/i.test(w);
    const FR_SUBJ = ["je", "tu", "il", "elle", "vous", "ils"];
    const frRefl = ["me", "te", "se", "se", "vous", "se"];


    /* ---------- German ---------- */

    const DE_IRR = {
      sein: ["bin", "bist", "ist", "sind", "seid", "sind"], haben: ["habe", "hast", "hat", "haben", "habt", "haben"], werden: ["werde", "wirst", "wird", "werden", "werdet", "werden"], wissen: ["weiß", "weißt", "weiß", "wissen", "wisst", "wissen"],
      "können": ["kann", "kannst", "kann", "können", "könnt", "können"], wollen: ["will", "willst", "will", "wollen", "wollt", "wollen"], "müssen": ["muss", "musst", "muss", "müssen", "müsst", "müssen"], "mögen": ["mag", "magst", "mag", "mögen", "mögt", "mögen"],
      "dürfen": ["darf", "darfst", "darf", "dürfen", "dürft", "dürfen"], sollen: ["soll", "sollst", "soll", "sollen", "sollt", "sollen"], "möchten": ["möchte", "möchtest", "möchte", "möchten", "möchtet", "möchten"],
    };
    const DE_VOWEL = { essen: "iss", geben: "gib", nehmen: "nimm", sehen: "sieh", lesen: "lies", helfen: "hilf", treffen: "triff", sprechen: "sprich", vergessen: "vergiss", werfen: "wirf", sterben: "stirb" };
    const DE_UML = { fahren: "fähr", schlafen: "schläf", laufen: "läuf", tragen: "träg", waschen: "wäsch", fallen: "fäll", halten: "hält" };
    const DE_PP = { essen: "gegessen", trinken: "getrunken", schlafen: "geschlafen", gehen: "gegangen", kommen: "gekommen", fahren: "gefahren", sehen: "gesehen", lesen: "gelesen", schreiben: "geschrieben", sprechen: "gesprochen", nehmen: "genommen", geben: "gegeben", treffen: "getroffen", helfen: "geholfen", tragen: "getragen", waschen: "gewaschen", vergessen: "vergessen", wissen: "gewusst", sein: "gewesen", haben: "gehabt", werden: "geworden", laufen: "gelaufen", schwimmen: "geschwommen", rufen: "gerufen", stehen: "gestanden", verstehen: "verstanden", bekommen: "bekommen", finden: "gefunden", singen: "gesungen", bleiben: "geblieben", denken: "gedacht", bringen: "gebracht", sitzen: "gesessen", liegen: "gelegen", fliegen: "geflogen", sterben: "gestorben", "können": "gekonnt", wollen: "gewollt", "müssen": "gemusst", "mögen": "gemocht", "anfangen": "angefangen", "anrufen": "angerufen", "aufstehen": "aufgestanden" };
    const DE_SEIN = new Set(["gehen", "kommen", "fahren", "laufen", "schwimmen", "sein", "werden", "bleiben", "fliegen", "sterben", "aufstehen", "aufwachen", "zurückkommen", "wandern", "reisen", "wachsen"]);
    const DE_SEP = ["zurück", "an", "aus", "auf", "ein", "mit", "ab", "los", "zu", "vor", "weg", "fern", "um"];
    const DE_SUBJ = ["ich", "du", "er", "sie", "wir", "ihr", "sie"];

    function deSplit(inf) {
      let refl = false, pre = "", v = inf, before = "";
      if (v.startsWith("sich ")) { refl = true; v = v.slice(5); }
      const parts = v.split(" ");
      if (parts.length > 1) { before = parts.slice(0, -1).join(" "); v = parts[parts.length - 1]; }
      for (const s of DE_SEP) {
        if (v.startsWith(s) && v.length > s.length + 3 && !DE_IRR[v]) { pre = s; v = v.slice(s.length); break; }
      }
      return { refl, pre, v, before };
    }

    function dePresent(v, p) {
      if (DE_IRR[v]) return DE_IRR[v][p];
      let st = v.replace(/e?n$/, "");
      const ep = /[dt]$/.test(st) || /([^aeioulrmnh])[mn]$/.test(st) ? "e" : "";
      if (p === 1 || p === 2) {
        if (DE_VOWEL[v]) st = DE_VOWEL[v];
        else if (DE_UML[v]) st = DE_UML[v];
        const vc = !!(DE_VOWEL[v] || DE_UML[v]);
        if (p === 1) return st + (/(s|ß|z|x)$/.test(st) ? "t" : (vc ? "" : ep) + "st");
        return st + (vc && /t$/.test(st) ? "" : (vc ? "" : ep) + "t");
      }
      if (p === 4) return st + ep + "t";
      if (p === 0) return st + "e";
      return v;
    }

    function dePP(v, pre) {
      const full = pre + v;
      if (DE_PP[full]) return DE_PP[full];
      if (DE_PP[v]) return pre + DE_PP[v];
      if (/^(be|ver|er|ent|zer|ge|emp|miss)/.test(v) || v.endsWith("ieren")) return pre + v.replace(/en$/, "t").replace(/n$/, "t");
      const st = v.replace(/e?n$/, "");
      return pre + "ge" + st + (/[dt]$/.test(st) ? "et" : "t");
    }

    function deImperative(v) {
      if (v === "sein") return "sei";
      if (v === "haben") return "hab";
      if (DE_VOWEL[v]) return DE_VOWEL[v];
      return v.replace(/e?n$/, "");
    }

    const DE_ACC = { der: "den", ein: "einen", mein: "meinen", dein: "deinen", sein: "seinen", ihr: "ihren", unser: "unseren", kein: "keinen" };


    /* ---------- English parsing ---------- */

    const PRON_PERSON = { i: 0, you: 1, he: 2, she: 2, it: 2, we: 3, "you all": 4, they: 5, everyone: 5 };
    const DET = new Set("a an the my your his her our their this that these those some more any".split(" "));
    const POSS = { my: "i", your: "you", his: "he", her: "she", our: "we", their: "they" };
    const WH = { what: "what", where: "where", when: "when", who: "who", how: "how", why: "why" };
    const AUXV = new Set("do does did is are am was were can could will would should have has had".split(" "));

    function lexOf(word) {
      return LEX[word] || null;
    }

    function isVerbWord(w) {
      for (const l of [w, PAST_EN[w], ...lemmas(w)]) {
        if (!l) continue;
        const v = LEX[l];
        if (v && v.s && /(ar|er|ir|ír)(se)?$/.test(v.s.split(" ").pop()) && !/^(el|la|los|las) /.test(v.s)) return l;
      }
      return null;
    }

    function nounOf(w) {
      for (const l of lemmas(w)) {
        const v = LEX[l];
        if (v && v.s && /^(el|la|los|las) /.test(v.s)) return l;
      }
      if (CORE[w] && KIN.has(w)) return w;
      return null;
    }

    function parse(text) {
      const raw = expand(text);
      if (!raw.length) return null;
      const P = { raw: text, q: /\?\s*$/.test(text), neg: false, tense: "pres", modal: null, subj: null, wh: null, verb: null, obj: null, objDet: null, objKin: false, time: [], place: null, placeType: null, withNP: null, forNP: null, adj: null, degree: null, imperative: false, lets: false, please: false, there: false, past: false, chunks: [], unknown: [] };
      let w = raw.join(" ").replace(/\byou guys\b|\by'all\b|\byou two\b/g, "you all").split(" ");

      if (w[0] === "please") { P.please = true; w = w.slice(1); }
      if (w[w.length - 1] === "please") { P.please = true; w = w.slice(0, -1); }

      let s = " " + w.join(" ") + " ";
      for (const t of TIME) {
        if (s.includes(" " + t + " ")) { P.time.push(t); s = s.replace(" " + t + " ", " "); }
      }
      w = s.trim().split(" ").filter(Boolean);

      if (w[0] === "let" && w[1] === "us") { P.lets = true; w = w.slice(2); }

      if (w[0] === "how" && w[1] === "much") { P.wh = "howmuch"; w = w.slice(2); }
      else if (w[0] === "how" && w[1] === "many") { P.wh = "howmany"; w = w.slice(2); }
      else if (WH[w[0]]) { P.wh = WH[w[0]]; w = w.slice(1); }

      if (w[0] === "is" && w[1] === "there" || w[0] === "are" && w[1] === "there") { P.there = true; P.q = true; w = w.slice(2); }
      if ((w[0] === "there") && (w[1] === "is" || w[1] === "are")) { P.there = true; w = w.slice(2); }

      let aux = null;
      if (AUXV.has(w[0]) && (P.q || P.wh)) { aux = w[0]; w = w.slice(1); P.q = true; }

      if (w[0] === "you" && w[1] === "all") { P.subj = "you all"; w = w.slice(2); }
      else if (PRON_PERSON[w[0]] !== undefined) { P.subj = w[0]; w = w.slice(1); }
      else if (POSS[w[0]] && nounOf(w[1] || "") && KIN.has(lemmas(w[1])[0] === "kids" ? "kids" : w[1])) { P.subj = w.slice(0, 2).join(" "); w = w.slice(2); }
      else if (w[0] && !aux && !P.wh && !P.lets && (isVerbWord(w[0]) || w[0] === "do" || w[0] === "be" || w[0] === "don" || (w[0] === "not"))) { P.imperative = true; }
      else if (!P.wh && !P.there && nounOf(w[0] || "") && (AUXV.has(w[1]) || isVerbWord(w[1] || ""))) { P.subj = w[0]; w = w.slice(1); }

      if (P.wh && ["is", "are", "was"].includes(aux) && !w.length && P.subj && P.subj.includes(" ") && P.subj !== "you all") {
        const [d0, n0] = P.subj.split(" ");
        P.whBe = { word: n0, det: d0 }; return P;
      }
      if (P.wh && ["is", "are", "was"].includes(aux) && w.length && !w.some(x => isVerbWord(x) && !nounOf(x))) {
        const save = w;
        let det = null;
        while (DET.has(w[0])) { det = det || w[0]; w = w.slice(1); }
        const n = w.join(" ");
        const cand = lemmas(n).find(l => LEX[l] || CORE[l]);
        if (cand) { P.whBe = { word: cand, det, plural: n !== cand && /s$/.test(n) }; return P; }
        w = save;
      }
      if (P.wh === "who" && !P.subj) P.subj = "who";

      if (!aux && AUXV.has(w[0])) { aux = w[0]; w = w.slice(1); }
      if (w[0] === "not") { P.neg = true; w = w.slice(1); }
      if (aux === "do" && P.imperative && P.neg) aux = null;

      if (aux === "did" || aux === "was" || aux === "were" || aux === "had") P.tense = "past";
      if (aux === "will") P.tense = "fut";
      if (aux === "can" || aux === "could") P.modal = "can";
      if (aux === "should") P.modal = "should";
      if (aux === "would" && (w[0] === "like" || w[0] === "love")) { P.modal = "want"; w = w.slice(1); if (w[0] === "to") w = w.slice(1); }
      if ((aux === "have" || aux === "has") && w[0] && (PAST_EN[w[0]] || /ed$|en$/.test(w[0]))) P.tense = "past";

      if (w[0] === "not") { P.neg = true; w = w.slice(1); }
      while (["really", "just", "usually", "still"].includes(w[0])) { if (w[0] === "really") P.really = true; w = w.slice(1); }

      if (w[0] === "going" && w[1] === "to") { P.tense = "fut"; w = w.slice(2); if (["am", "is", "are"].includes(aux)) aux = null; }
      const MODALS = [["want", "to", "want"], ["wanted", "to", "want"], ["need", "to", "need"], ["needed", "to", "need"], ["have", "to", "need"], ["has", "to", "need"], ["had", "to", "need"], ["like", "to", "like"], ["love", "to", "like"], ["try", "to", "try"]];
      for (const [a, b, m] of MODALS) {
        if (w[0] === a && w[1] === b) { P.modal = P.modal || m; if (["wanted", "needed", "had"].includes(a)) P.tense = "past"; w = w.slice(2); break; }
      }

      const ab = new Set(["am", "is", "are", "was", "were", "be"]);
      if ((ab.has(aux) || ab.has(w[0])) && (w[ab.has(w[0]) ? 1 : 0] === "going" && w[ab.has(w[0]) ? 2 : 1] === "to")) {
        w = w.slice(ab.has(w[0]) ? 3 : 2); P.tense = "fut"; aux = null;
        if (w[0] === "not") { P.neg = true; w = w.slice(1); }
      }
      if ((ab.has(aux) || ab.has(w[0])) && (ab.has(w[0]) ? w[1] : w[0]) && /ing$/.test(ab.has(w[0]) ? w[1] : w[0]) && isVerbWord(ab.has(w[0]) ? w[1] : w[0])) {
        if (ab.has(w[0])) { if (w[0] === "was" || w[0] === "were") P.tense = "past"; w = w.slice(1); }
        if (w[0] === "not") { P.neg = true; w = w.slice(1); }
        const pv = isVerbWord(w[0]);
        const futT = P.time.some(t => /tomorrow|tonight|next|later|soon|weekend/.test(t));
        P.prog = P.tense !== "past" && P.wh !== "when" && !futT;
        if (!P.prog && P.tense !== "past" && futT) P.tense = "fut";
        P.motionProg = P.prog && MOTION.has(pv);
        if (P.motionProg && P.time.length) { P.prog = false; P.motionNow = true; }
        aux = null;
      }
      else if (ab.has(aux) || ab.has(w[0])) {
        if (ab.has(w[0])) { if (w[0] === "was" || w[0] === "were") P.tense = "past"; w = w.slice(1); }
        if (w[0] === "not") { P.neg = true; w = w.slice(1); }
        const degs = ["very", "so", "too", "really", "a", "little", "bit"];
        while (degs.includes(w[0])) {
          if (w[0] === "a" && (w[1] === "little" || w[1] === "bit")) { P.degree = "a little"; w = w.slice(2); continue; }
          if (w[0] === "a") break;
          P.degree = P.degree || w[0]; w = w.slice(1);
        }
        if (w[0] && ADJ.has(w[0]) && !isVerbWord(w[0] + "")) {
          P.adj = w[0]; w = w.slice(1);
        } else if (w[0] && /ing$/.test(w[0]) && isVerbWord(w[0])) {
          P.prog = true;
        } else if (w[0] && ADJ.has(w[0])) {
          P.adj = w[0]; w = w.slice(1);
        } else if (P.there) {
        } else if (w.length) {
          P.copula = true;
        }
      }

      if (!P.adj && !P.copula && !P.there) {
        const vw = w[0] && isVerbWord(w[0]);
        if (vw) {
          P.verb = vw;
          if (PAST_EN[w[0]] || (/ed$/.test(w[0]) && w[0] !== vw && aux !== "have")) { if (!P.modal || P.modal === "need") P.tense = P.modal ? P.tense : "past"; }
          if (aux === "have" || aux === "has") P.tense = "past";
          w = w.slice(1);
          if ((w[0] === "down" || w[0] === "up") && ["sit", "stand", "calm", "lie", "wake", "get", "hurry", "shut"].includes(P.verb)) w = w.slice(1);
          if (w[0] === "well") { P.well = true; w = w.slice(1); }
          if (w[0] === "up" || w[0] === "out" || w[0] === "off" || w[0] === "on") {
            const ph = P.verb + " " + w[0];
            if (LEX[ph] || CORE[ph]) { P.verb = ph; w = w.slice(1); }
          }
        } else if (P.modal === "want" || P.modal === "need" || P.modal === "like") {
          P.verb = { want: "want", need: "need", like: "like" }[P.modal];
          P.modal = null;
        } else if (aux === "have" || aux === "has" || w[0] === "have" || w[0] === "has") {
          P.verb = "have";
          if (w[0] === "have" || w[0] === "has") w = w.slice(1);
        }
      }

      const np = () => {
        let det = null, adj = [];
        while (DET.has(w[0])) { det = det || w[0]; w = w.slice(1); }
        while (w[0] && ADJ.has(w[0]) && w[1] && nounOf(w[1])) { adj.push(w[0]); w = w.slice(1); }
        if (!w[0]) return null;
        if (CORE[w[0]] && PRON_PERSON[w[0]] === undefined && ["me", "him", "her", "us", "them", "you"].includes(w[0])) { const x = w[0]; w = w.slice(1); return { pron: x }; }
        if (w[0] === "home" || w[0] === "here" || w[0] === "there") { const x = w[0]; w = w.slice(1); return { word: x, det, adj }; }
        let best = null;
        for (let n = Math.min(3, w.length); n >= 1; n--) {
          const span = w.slice(0, n).join(" ");
          const cand = lemmas(span).find(l => LEX[l] || CORE[l]);
          if (cand) { best = { word: cand, n, plural: span !== cand && /s$/.test(span) }; break; }
        }
        if (!best) { P.unknown.push(w[0]); w = w.slice(1); return null; }
        w = w.slice(best.n);
        return { word: best.word, det, adj, plural: best.plural };
      };

      if (P.there) { while (w[0] === "any" || w[0] === "some") w = w.slice(1); P.obj = np(); }
      const ADV = new Set(["together", "too", "also", "well", "yet", "now", "here", "there", "later", "again", "already", "home"]);
      if ((P.verb || P.copula) && ["it", "this", "that"].includes(w[0]) && (!w[1] || ADV.has(w[1]) || ["with", "to", "at", "for"].includes(w[1]))) { P.objDem = w[0]; w = w.slice(1); }
      if ((P.modal === "need" || P.verb === "need") && P.verb === "help" && !w.length) { P.verb = "need"; P.modal = null; P.obj = { word: "help n" }; }
      if (P.verb === "need" && w[0] === "help") { P.obj = { word: "help n" }; w = w.slice(1); }
      if (["anything", "something"].includes(w[0])) { P.obj = { word: w[0] }; w = w.slice(1); }
      if (P.verb || P.copula) {
        if (P.verb === "call" || P.verb === "help" || P.verb === "visit" || P.verb === "tell" || P.verb === "ask" || P.verb === "teach" || P.verb === "meet" || P.verb === "miss" || P.verb === "love" || P.verb === "like" || P.verb === "see") {
          if (w[0] === "you" && w[1] === "all") { P.objPron = "you all"; w = w.slice(2); }
          else if (["me", "you", "him", "her", "us", "them"].includes(w[0])) { P.objPron = w[0]; w = w.slice(1); }
        }
        if (!P.obj && !P.objDem && w[0] && !["to", "at", "in", "with", "for", "from", "on"].includes(w[0]) && !ADV.has(w[0])) P.obj = np();
      }

      while (w.length) {
        const h = w[0];
        if (h === "to" || h === "at" || h === "in" || h === "from") {
          w = w.slice(1);
          if (w[0] === "the" && w[1] === "store") { w = w.slice(1); }
          const n = np();
          if (n) { P.place = n; P.placeType = h; }
        } else if (h === "with") {
          w = w.slice(1);
          if (["me", "you", "him", "her", "us", "them"].includes(w[0])) { P.withNP = { pron: w[0] }; w = w.slice(1); }
          else P.withNP = np();
        } else if (h === "for") {
          w = w.slice(1);
          if (["me", "you", "him", "her", "us", "them"].includes(w[0])) { P.forNP = { pron: w[0] }; w = w.slice(1); }
          else P.forNP = np();
        } else if (h === "together") { P.together = true; w = w.slice(1); }
        else if (h === "too" || h === "also") { P.also = true; w = w.slice(1); }
        else if (h === "a" && w[1] === "lot") { P.alot = true; w = w.slice(2); }
        else if (h === "home" && !P.place) { P.place = { word: "home" }; P.placeType = "to"; w = w.slice(1); }
        else if (h === "here" || h === "there") { P.place = { word: h }; P.placeType = "at"; w = w.slice(1); }
        else if (h === "yet") { P.yet = true; w = w.slice(1); }
        else if (h === "well") { P.well = true; w = w.slice(1); }
        else if (h === "more" && !P.obj) { P.more = true; w = w.slice(1); }
        else if (!P.obj && !P.objDem && (P.verb || P.copula) && !ADV.has(h)) { P.obj = np(); }
        else { P.unknown.push(h); w = w.slice(1); }
      }

      if (P.wh === "where" && !P.place && P.verb) { P.place = { word: "where" }; P.placeType = MOTION.has(P.verb) ? "to" : "at"; }
      if (MOTION.has(P.verb) && P.obj && !P.place && (P.verb === "go" || P.obj.word === "home")) { P.place = P.obj; P.placeType = "to"; P.obj = null; }
      if (P.verb === "have" && P.obj && MEALS[P.obj.word]) P.verb = "eat";
      if (P.verb === "eat" && P.obj && MEALS[P.obj.word]) P.meal = P.obj.word;
      if (P.verb === "want" && (P.obj || P.wh === "what")) P.wantN = true;

      if (!P.verb && !P.adj && !P.copula && !P.there) return null;
      if (P.unknown.length > 1) return null;
      return P;
    }


    /* ---------- output helpers ---------- */

    function zhWord(key) {
      if (CORE[key]) return CORE[key];
      const v = LEX[key];
      if (v && v.y && v.m) return { yue: [v.y[0], v.y[1], v.y[2] === 1], cmn: [v.m[0], v.m[1]], tsn: v.t ? [v.t[0], v.t[1], false] : null, dict: v.y[2] !== 1 };
      const p = WORDS.get(key);
      if (p) {
        const one = l => p[l] && p[l].length ? [p[l].map(t => t.hz).join(""), p[l].map(t => t.rom).join(" "), true] : null;
        return { yue: one("yue"), cmn: one("cmn"), tsn: one("tsn") };
      }
      return null;
    }

    const EUX = {
      cantonese: ["cantonés", "le cantonais", "Kantonesisch"], mandarin: ["mandarín", "le mandarin", "Mandarin"], taishanese: ["taishanés", "le taïshanais", "Taishanesisch"],
      english: ["inglés", "l'anglais", "Englisch"], chinese: ["chino", "le chinois", "Chinesisch"], spanish: ["español", "l'espagnol", "Spanisch"], french: ["francés", "le français", "Französisch"], german: ["alemán", "l'allemand", "Deutsch"],
      sit: ["sentarse", "s'asseoir", "sich setzen"], "go out": ["salir", "sortir", "ausgehen"], bathroom: ["el baño", "les toilettes", "die Toilette"], key: ["la llave", "la clé", "der Schlüssel"],
    };

    function euWord(key, lang) {
      if (EUX[key]) return EUX[key][{ es: 0, fr: 1, de: 2 }[lang]];
      const v = LEX[key];
      const k = { es: "s", fr: "f", de: "d" }[lang];
      return v && v[k] ? v[k] : null;
    }

    function build(P) {
      const G = [];
      const gl = (en) => { G.push(en); return G.length - 1; };

      const subjKey = P.subj ? (P.subj.includes(" ") && POSS[P.subj.split(" ")[0]] ? P.subj : P.subj) : (P.imperative || P.lets ? null : "you");
      const person = P.lets ? 3 : (P.subj ? (PRON_PERSON[P.subj] ?? 2) : 1);

      const ix = {};
      if (P.wh && P.wh !== "who") ix.wh = gl({ what: "what", where: "where", when: "when", how: "how", why: "why", howmuch: "how much", howmany: "how many" }[P.wh]);
      if (P.lets) ix.lets = gl("let's");
      if (P.please) ix.please = gl("please");
      if (P.subj && P.subj !== "who") ix.subj = gl(P.subj === "i" ? "I" : P.subj);
      if (P.subj === "who") ix.subj = gl("who");
      if (P.neg) ix.neg = gl(P.tense === "past" ? "didn't" : P.imperative ? "don't" : "not");
      if (P.modal) ix.modal = gl({ want: "want to", can: "can", need: "need to", should: "should", like: "like to", try: "try to" }[P.modal]);
      if (P.tense === "fut" && !P.modal) ix.fut = gl("will");
      const pastOf = v => { const k = Object.keys(PAST_EN).find(x => PAST_EN[x] === v && !/ed$/.test(x)); return k || (v.endsWith("e") ? v + "d" : v + "ed"); };
      if (P.verb) ix.verb = gl(P.tense === "past" && !P.modal && !P.neg && !(P.q && !P.wh) ? (P.verb.includes(" ") ? pastOf(P.verb.split(" ")[0]) + " " + P.verb.split(" ").slice(1).join(" ") : pastOf(P.verb)) : P.verb.replace(/ n$/, ""));
      if (P.adj) ix.adj = gl((P.degree ? P.degree + " " : "") + P.adj);
      if (P.copula) ix.cop = gl("is");
      if (P.there) ix.there = gl("there is");
      if (P.objPron) ix.objPron = gl(P.objPron);
      if (P.obj) ix.obj = gl(((P.obj.det && P.obj.det !== "the" && P.obj.det !== "a" && P.obj.det !== "an") ? P.obj.det + " " : "") + (P.obj.adj && P.obj.adj.length ? P.obj.adj.join(" ") + " " : "") + (P.obj.word || P.obj.pron));
      if (P.more) ix.more = gl("more");
      if (P.objDem) ix.objDem = gl(P.objDem);
      if (P.really) ix.really = gl("really");
      if (P.place) ix.place = gl((P.placeType === "to" && P.place.word !== "home" && P.place.word !== "where" ? "to " : P.placeType === "at" && P.place.word !== "here" && P.place.word !== "there" && P.place.word !== "where" ? "at " : "") + (P.place.word === "where" ? "where" : (P.place.det && P.place.det !== "the" ? P.place.det + " " : "") + P.place.word));
      if (P.withNP) ix.with = gl("with " + (P.withNP.pron || ((P.withNP.det && P.withNP.det !== "the" ? P.withNP.det + " " : "") + P.withNP.word)));
      if (P.forNP) ix.for = gl("for " + (P.forNP.pron || P.forNP.word));
      P.time.forEach((t, k) => { ix["time" + k] = gl(t); });
      if (P.together) ix.together = gl("together");
      if (P.also) ix.also = gl("too");
      if (P.alot) ix.alot = gl("a lot");
      if (P.yet) ix.yet = gl("yet");
      if (P.q && !P.wh) ix.q = gl("(question)");

      const out = { gloss: G.map((g, k) => k === 0 ? g.charAt(0).toUpperCase() + g.slice(1) : g) };
      let miss = 0;
      ["yue", "cmn", "tsn"].forEach(l => { out[l] = zhBuild(P, l, ix, () => miss++); });
      out.es = esBuild(P, ix, person);
      out.fr = frBuild(P, ix, person);
      out.de = deBuild(P, ix, person);
      out.miss = miss;
      return out;
    }


    /* ---------- Chinese (Cantonese, Mandarin, Taishanese) ---------- */

    function zhBuild(P, L, ix, missing) {
      const toks = [];
      const put = (w, ref, sure) => {
        if (!w) return;
        const x = w[L];
        if (!x || !x[0]) return;
        toks.push({ hz: x[0], rom: x[1], refs: ref === undefined || ref === null ? [] : [].concat(ref), sure: sure === false ? false : x[2] !== false });
      };
      const word = (key, ref) => {
        const z = zhWord(key);
        if (!z || !z[L]) { missing(); toks.push({ hz: "（" + key + "）", rom: "", refs: [ref], sure: false }); return; }
        put(z, ref);
      };
      const npZh = (n, ref) => {
        if (!n) return;
        if (n.pron) return word(n.pron, ref);
        if (n.word === "where") return put(CORE.where, ref);
        const owner = n.det && POSS[n.det];
        if (owner) { word(owner, ref); if (!KIN.has(n.word)) put(FN.of, ref); }
        if (n.det === "this") put(FN.this, ref);
        if (n.det === "that") put(FN.that, ref);
        if (n.det === "some") put(FN.some, ref);
        if (n.det === "more") put(FN.more, ref);
        (n.adj || []).forEach(a => { word(a, ref); if (L === "cmn") put(FN.of, ref); });
        word(n.word, ref);
      };
      const timeAll = () => P.time.forEach((t, k) => { const x = TIME_X[t]; put({ yue: x[0], cmn: x[1], tsn: x[2] }, ix["time" + k]); });

      const yesno = P.q && !P.wh;
      let aNotA = yesno && L !== "cmn";

      if (P.wh === "why") put(CORE.why, ix.wh);
      if (P.lets && L !== "cmn") { put(CORE.we, ix.lets); }
      if (P.lets && L === "cmn") { put(CORE.we, ix.lets); }

      const timeFirst = P.time.length && !P.subj;
      if (timeFirst) timeAll();
      if (P.subj === "it" && P.adj) {}
      else if (P.subj) {
        if (P.subj === "who") put(CORE.who, ix.subj);
        else if (P.subj.includes(" ")) npZh({ det: P.subj.split(" ")[0], word: P.subj.split(" ")[1] }, ix.subj);
        else word(P.subj, ix.subj);
      } else if (!P.imperative && !P.lets && !P.there && !P.adj) {
      }
      if (!timeFirst) timeAll();
      if (P.also) put(FN.too.cmn ? CORE.also : CORE.also, ix.also);
      if (P.wh === "when") put(CORE.when, ix.wh);
      if (P.wh === "how" && P.verb) put(CORE.how, ix.wh);

      const preVerb = () => {
        if (P.withNP) { put(FN.with, ix.with); npZh(P.withNP, ix.with); put(FN.togetherV, ix.with); }
        if (P.together && !P.withNP) put(CORE.together, ix.together);
        if (P.place && P.placeType !== "to") { put(FN.at, ix.place); npZh(P.place, ix.place); }
        if (P.prog && L === "cmn" && !P.neg) put(P.motionProg ? { cmn: ["要", "yào"] } : { cmn: ["在", "zài"] }, ix.verb);
      };
      if (P.adj || P.there || P.copula) preVerb();

      const neg = P.neg ? (P.tense === "past" ? FN.notPast : P.tense === "fut" ? FN.notWill : FN.not) : null;
      if (P.imperative && P.neg) {
        put({ yue: ["唔好", "m4 hou2"], cmn: ["别", "bié"], tsn: ["唔好", "mɔu55"] }, ix.neg);
      }

      const modal = (P.tense === "fut" && P.neg && !P.modal) ? null : P.modal ? { want: FN.want, can: (SKILL.has(P.verb) ? FN.know : FN.can), need: FN.need, should: FN.should, like: FN.like, try: { yue: ["試吓", "si3 haa5"], cmn: ["试试", "shì shi"], tsn: ["試下", "si33 ha21", false] } }[P.modal] : (P.tense === "fut" ? FN.will : null);

      if (P.motionProg && P.neg && L !== "cmn") { put(FN.notWill, ix.neg); }
      const aNotAWord = (w, ref) => {
        const x = w[L];
        if (!x) return;
        const first = [...x[0]][0];
        const fr = x[1].split(" ")[0];
        const neg = L === "tsn" ? ["唔", "m22"] : ["唔", "m4"];
        toks.push({ hz: first + neg[0] + x[0], rom: fr + " " + neg[1] + " " + x[1], refs: [].concat(ref), sure: x[2] !== false });
      };

      if (P.adj && ["ready", "done", "finished"].includes(P.adj)) {
        const R = { yue: ["準備好", "zeon2 bei6 hou2"], cmn: ["准备好", "zhǔn bèi hǎo"], tsn: ["準備好", "dzun55 bi32 hɔu55", false] }[L];
        if (P.neg) toks.push({ hz: L === "cmn" ? "还没" : L === "tsn" ? "還唔曾" : "仲未", rom: L === "cmn" ? "hái méi" : L === "tsn" ? "van21 miaŋ21" : "zung6 mei6", refs: [ix.neg], sure: L !== "tsn" });
        toks.push({ hz: R[0], rom: R[1], refs: [ix.adj], sure: R[2] !== false });
        if (yesno) toks.push(L === "cmn" ? { hz: "了吗", rom: "le ma", refs: [ix.q], sure: true } : L === "tsn" ? { hz: "唔曾", rom: "miaŋ21", refs: [ix.q], sure: true } : { hz: "未呀", rom: "mei6 aa3", refs: [ix.q], sure: true });
        else if (!P.neg) toks.push(L === "cmn" ? { hz: "了", rom: "le", refs: [ix.adj], sure: true } : L === "tsn" ? { hz: "啦", rom: "la55", refs: [ix.adj], sure: true } : { hz: "喇", rom: "laa3", refs: [ix.adj], sure: true });
        return toks;
      }
      if (P.adj && P.adj === "good" && P.subj === "it" && !P.degree && !yesno && !P.neg && L === "yue") { toks.push({ hz: "好正", rom: "hou2 zeng3", refs: [ix.adj], sure: true }); return toks; }
      if (P.adj) {
        const adjW = zhWord(P.adj);
        if (P.neg && !P.imperative) put(FN.not, ix.neg);
        if (yesno && !P.neg && L !== "cmn") { if (adjW) aNotAWord(adjW, ix.adj); else word(P.adj, ix.adj); }
        else {
          const deg = P.degree === "too" ? FN.too : P.degree === "a little" ? { yue: ["有啲", "jau5 di1"], cmn: ["有点", "yǒu diǎn"], tsn: ["有啲", "yiu33 nit55", false] } : (!P.neg && !(yesno && L === "cmn" && !P.degree) ? FN.very : null);
          if (deg) put(deg, ix.adj);
          if (adjW) put(adjW, ix.adj); else word(P.adj, ix.adj);
        }
        if (yesno && (L === "cmn" || P.neg)) put(FN.q, ix.q);
        else if (yesno) put(FN.q, ix.q);
        else if (P.wh) put(FN.qWh, null);
        return toks;
      }

      if (P.there) {
        if (yesno) put(FN.haveNot, ix.there); else put(FN.have, ix.there);
        npZh(P.obj, ix.obj);
        if (P.place) {}
        if (yesno) put(L === "cmn" ? { cmn: ["", ""] } : FN.q, ix.q);
        return toks;
      }

      if (P.copula) {
        if (P.neg) put(FN.not, ix.neg);
        if (yesno && L !== "cmn" && !P.neg) aNotAWord(FN.be, ix.cop); else put(FN.be, ix.cop);
        if (P.wh === "what" && !P.obj) put(CORE.what, ix.wh);
        npZh(P.obj, ix.obj);
        if (P.wh === "who" && P.subj !== "who") put(CORE.who, ix.wh);
        if (P.wh === "where") put(CORE.where, ix.wh);
        if (yesno) put(FN.q, ix.q); else if (P.wh) put(FN.qWh, null);
        return toks;
      }

      const pastYesNo = yesno && P.tense === "past" && !P.modal;
      if (pastYesNo && !P.yet && !P.well) put(FN.haveNot, ix.q);

      if (neg && !(P.imperative) && !(P.modal === "can" && ["find", "see", "hear", "sleep"].includes(P.verb))) {
        if (P.motionProg && L !== "cmn") {}
        else if (P.modal || P.tense !== "past") put(neg, ix.neg); else put(FN.notPast, ix.neg);
      }

      const RES = { find: { yue: ["搵", "wan2"], cmn: ["找", "zhǎo"], tsn: ["搵", "vun55"] }, see: { yue: ["睇", "tai2"], cmn: ["看", "kàn"], tsn: ["睇", "hai55"] }, hear: { yue: ["聽", "teng1"], cmn: ["听", "tīng"], tsn: ["聽", "hiaŋ33"] }, sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] } };
      const resV = P.modal === "can" && RES[P.verb];
      if (resV) {
        preVerb();
        const st = resV[L];
        const mid = P.neg ? (L === "cmn" ? ["不", "bu"] : L === "tsn" ? ["唔", "m22"] : ["唔", "m4"]) : (L === "cmn" ? ["得", "de"] : L === "tsn" ? ["得", "ak33"] : ["得", "dak1"]);
        const endc = L === "cmn" ? (P.verb === "see" ? ["见", "jiàn"] : ["到", "dào"]) : L === "tsn" ? ["到", "ɔu55"] : ["到", "dou2"];
        if (yesno && !P.neg && L !== "cmn") toks.push({ hz: st[0] + "唔" + st[0] + "得到", rom: st[1] + (L === "tsn" ? " m22 " : " m4 ") + st[1] + " " + (L === "tsn" ? "ak33 ɔu55" : "dak1 dou2"), refs: [ix.modal, ix.verb], sure: L !== "tsn" });
        else toks.push({ hz: st[0] + mid[0] + endc[0], rom: st[1] + " " + mid[1] + " " + endc[1], refs: [ix.modal, ix.neg, ix.verb].filter(x => x !== undefined), sure: L !== "tsn" });
        npZh(P.obj, ix.obj);
        if (yesno) put(FN.q, ix.q); else if (P.wh) put(FN.qWh, null);
        return toks;
      }

      if (modal) {
        if (aNotA && !P.neg && !pastYesNo) { aNotAWord(modal, ix.modal ?? ix.fut); aNotA = false; }
        else put(modal, ix.modal ?? ix.fut);
      }
      preVerb();

      if (P.lets && L === "yue") {}
      if (P.place && P.placeType === "to" && P.verb !== "go" && P.verb !== "come") {
        if (MOTION.has(P.verb) || P.verb === "eat" || P.verb === "buy" || P.verb === "swim" || P.verb === "play" || P.verb === "watch") {
          put(FN.go, ix.place);
          npZh(P.place, ix.place);
        }
      }

      if (P.verb) {
        const homeV = { go: { yue: ["返", "faan1"], cmn: ["回", "huí"], tsn: ["返", "fan33"] }, come: { yue: ["返嚟", "faan1 lai4"], cmn: ["回", "huí"], tsn: ["返來", "fan33 lɔi22"] } };
        const goHome = P.place && P.place.word === "home" && homeV[P.verb];
        if (P.well && P.neg) {
          const st0 = { sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] }, eat: { yue: ["食", "sik6"], cmn: ["吃", "chī"], tsn: ["吃", "hiak33"] } }[P.verb] || zhWord(P.verb);
          const x0 = st0 && st0[L];
          if (x0) {
            const n = toks.findIndex(t => /^(冇|没|唔|不)$/.test(t.hz));
            if (n >= 0) toks.splice(n, 1);
            if (L === "cmn") toks.push({ hz: "没" + x0[0] + "好", rom: "méi " + x0[1].split(" ")[0] + " hǎo", refs: [ix.neg, ix.verb], sure: true });
            else toks.push({ hz: x0[0] + "得唔好", rom: x0[1].split(" ")[0] + (L === "tsn" ? " ak33 m22 hɔu55" : " dak1 m4 hou2"), refs: [ix.verb, ix.neg], sure: true });
            return toks;
          }
        }
        if (P.well) {
          const st = { sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] }, eat: { yue: ["食", "sik6"], cmn: ["吃", "chī"], tsn: ["吃", "hiak33"] } }[P.verb] || zhWord(P.verb);
          const x = st && st[L];
          if (x) {
            const de = L === "cmn" ? ["得", "de"] : L === "tsn" ? ["得", "ak33"] : ["得", "dak1"];
            const good = L === "cmn" ? ["好", "hǎo"] : L === "tsn" ? ["好", "hɔu55"] : ["好", "hou2"];
            const tail = yesno ? (L === "cmn" ? good : [good[0] + "唔" + good[0], good[1] + (L === "tsn" ? " m22 " : " m4 ") + good[1]]) : good;
            toks.push({ hz: x[0] + de[0] + tail[0], rom: x[1].split(" ")[0] + " " + de[1] + " " + tail[1], refs: [ix.verb], sure: true });
            if (yesno) put(FN.q, ix.q);
            return toks;
          }
        }
        if (P.verb === "eat" && pastYesNo && !P.obj && !P.wh) {
          const ate = { yue: [["你", "nei5"], ["食咗飯", "sik6 zo2 faan6"], ["未呀", "mei6 aa3"]], cmn: [["你", "nǐ"], ["吃饭", "chī fàn"], ["了吗", "le ma"]], tsn: [["你", "ni33"], ["吃啊飯", "hiak33 ə33 fan32"], ["唔曾", "miaŋ21"]] }[L];
          toks.length = 0;
          if (P.subj && P.subj !== "you") { const z = zhWord(P.subj); if (z) toks.push({ hz: z[L][0], rom: z[L][1], refs: [ix.subj], sure: true }); } else toks.push({ hz: ate[0][0], rom: ate[0][1], refs: [ix.subj], sure: true });
          toks.push({ hz: ate[1][0], rom: ate[1][1], refs: [ix.verb], sure: true });
          toks.push({ hz: ate[2][0], rom: ate[2][1], refs: [ix.q], sure: true });
          return toks;
        }
        if (P.really && P.verb === "like") put({ yue: ["真係好", "zan1 hai6 hou2"], cmn: ["非常", "fēi cháng"], tsn: ["真係好", "tsin33 hai32 hɔu55", false] }, ix.really);
        let vw = goHome ? homeV[P.verb] : P.wantN ? (P.wh === "what" ? { yue: ["想要", "soeng2 jiu3"], cmn: ["想要", "xiǎng yào"], tsn: ["想要", "ɬiaŋ55 yiau33", false] } : { yue: ["要", "jiu3"], cmn: ["要", "yào"], tsn: ["要", "yiau33", false] }) : P.verb === "cook" && (P.obj || P.objDem) ? { yue: ["煮", "zyu2"], cmn: ["做", "zuò"], tsn: ["煮", "dzi55"] } : zhWord(P.verb);
        const isGoCome = P.verb === "go" || P.verb === "come";
        if (aNotA && !P.neg && !pastYesNo && vw && !P.yet && !P.prog) { aNotAWord(vw, ix.verb); aNotA = false; }
        else if (vw) put(vw, ix.verb); else word(P.verb, ix.verb);
        if (P.tense === "past" && !P.neg && !P.modal && !pastYesNo && !(L === "cmn" && !P.obj && !P.objDem && !P.wh) || (P.tense === "past" && !P.neg && !P.modal && P.yet && L !== "cmn")) put(FN.past, ix.verb);
        if (P.prog && L !== "cmn" && !P.neg) put({ yue: ["緊", "gan2"], tsn: ["緊", "gin55", false] }, ix.verb);
        if (P.objDem) put({ it: (P.verb === "like" && !yesno) ? CORE.it : null, this: FN.this, that: FN.that }[P.objDem] || { yue: null, cmn: null, tsn: null }, ix.objDem);
        if (!P.obj && !P.objDem && !P.wh && !P.place && !P.objPron && ["eat"].includes(P.verb) && !P.neg && !P.prog === false) put({ yue: ["嘢", "je5"], cmn: ["东西", "dōng xi"], tsn: ["嘢", "yia33"] }, ix.verb);
        else if (!P.obj && !P.objDem && !P.wh && !P.place && P.verb === "eat" && (P.modal === "want") && !P.neg) put({ yue: ["嘢", "je5"], cmn: ["东西", "dōng xi"], tsn: ["嘢", "yia33"] }, ix.verb);
        if (P.objPron) word(P.objPron, ix.objPron);
        if (isGoCome && P.place && !(goHome && L === "cmn" && false)) npZh(goHome && L === "cmn" ? { word: "home" } : P.place, ix.place);
        if (P.wh === "what" && !P.obj) put(CORE.what, ix.wh);
        if (P.wh === "where" && isGoCome && !P.place) put(CORE.where, ix.wh);
        if (P.wh === "who" && P.subj !== "who" && !P.obj) put(CORE.who, ix.wh);
        if (P.wh === "howmany") put(FN.howMany, ix.wh);
        if (P.more && !P.obj) put(FN.more, ix.more);
        npZh(P.obj, ix.obj);
        if (P.forNP) { }
        if (P.alot) put(CORE["a lot"], ix.alot);
        if (P.tense === "past" && !P.neg && !P.modal && L === "cmn" && !pastYesNo && !P.obj && !P.objDem && !P.wh) put(FN.past, ix.verb);
      }

      if (P.wh === "howmuch") put(FN.howMuch, ix.wh);

      if (P.yet && yesno) put(FN.yet, ix.yet);
      else if (yesno) {
        if (L === "cmn") put(pastYesNo ? { cmn: ["", ""] } : FN.q, ix.q);
        else put(FN.q, ix.q);
      } else if (P.wh) put(FN.qWh, null);
      else if (P.lets) put(FN.lets, ix.lets);
      if (P.please) {
        const pz = { yue: ["唔該", "m4 goi1"], cmn: ["请", "qǐng"], tsn: ["唔該", "m22 gɔi33"] }[L];
        toks.unshift({ hz: pz[0], rom: pz[1], refs: [ix.please], sure: true });
      }

      return toks;
    }


    /* ---------- Spanish ---------- */

    function npEU(n, lang, role, P) {
      if (!n) return "";
      if (n.word === "home") return { es: role === "to" ? "a casa" : "en casa", fr: role === "to" ? "à la maison" : "à la maison", de: role === "to" ? "nach Hause" : "zu Hause" }[lang];
      if (n.word === "here") return { es: "aquí", fr: "ici", de: "hier" }[lang];
      if (n.word === "there") return { es: "allí", fr: "là-bas", de: "dort" }[lang];
      if (n.pron) {
        const T = { es: { me: "mí", you: "ti", him: "él", her: "ella", us: "nosotros", them: "ellos" }, fr: { me: "moi", you: "toi", him: "lui", her: "elle", us: "nous", them: "eux" }, de: { me: "mir", you: "dir", him: "ihm", her: "ihr", us: "uns", them: "ihnen" } };
        return T[lang][n.pron] || n.pron;
      }
      let base = euWord(n.word, lang);
      if (!base) return "";
      const m = base.match(/^(los|las|les|el|la|le|der|die|das) (.*)$/);
      let art = m ? m[1] : "", noun = m ? m[2] : base;
      if (lang === "fr" && base.startsWith("l'")) { art = "l'"; noun = base.slice(2); }
      const poss = n.det && POSS[n.det];
      const adj = (n.adj || []).map(a => euWord(a, lang)).filter(Boolean);
      if (n.plural && !/^(los|las|les)$/.test(art) && lang !== "de") {
        if (lang === "es") { noun = noun.split(" ").map((x, i) => i === 0 ? (/[aeiou]$/.test(x) ? x + "s" : x + "es") : x).join(" "); art = art === "la" ? "las" : "los"; }
        if (lang === "fr") { noun = noun.split(" ").map((x, i) => i === 0 && !/[sxz]$/.test(x) ? x + "s" : x).join(" "); art = "les"; }
      }
      if (n.plural && lang === "de") { noun = DE_PL[noun] || noun; art = "die"; }

      if (lang === "es") {
        const pl = /^(los|las)$/.test(art);
        if (poss) art = { i: "mi", you: "tu", he: "su", she: "su", we: "nuestro", they: "su" }[poss] + (pl ? "s" : "");
        else if (n.det === "this") art = art === "la" ? "esta" : art === "las" ? "estas" : art === "los" ? "estos" : "este";
        else if (n.det === "that") art = art === "la" ? "esa" : "ese";
        else if (n.det === "a" || n.det === "an") art = art === "la" ? "una" : "un";
        else if (n.det === "some") art = art === "la" || art === "las" ? "unas" : "unos";
        else if (n.det === "more") art = "más";
        else if (!n.det && role === "obj" && !MEALS[n.word]) art = "";
        if (LANGS.has(n.word) && !n.det) art = "";
        let s = [art, noun, ...adj].filter(Boolean).join(" ");
        if (role === "to") s = (art === "el" ? "al " + noun : "a " + s);
        if (role === "at") s = "en " + s;
        if (role === "with") s = "con " + s;
        if (role === "for") s = "para " + s;
        return s;
      }

      if (lang === "fr") {
        const pl = art === "les";
        const fem = art === "la";
        const vowel = elide(noun);
        if (poss) art = pl ? { i: "mes", you: "tes", he: "ses", she: "ses", we: "nos", they: "leurs" }[poss] : (fem && !vowel ? { i: "ma", you: "ta", he: "sa", she: "sa", we: "notre", they: "leur" }[poss] : { i: "mon", you: "ton", he: "son", she: "son", we: "notre", they: "leur" }[poss]);
        else if (n.det === "this" || n.det === "that") art = pl ? "ces" : fem ? "cette" : vowel ? "cet" : "ce";
        else if (n.det === "a" || n.det === "an") art = fem ? "une" : "un";
        else if (n.det === "more") art = "plus de";
        else if (!n.det && role === "obj" && P && !["like", "love", "hate"].includes(P.verb) && !MEALS[n.word] && !LANGS.has(n.word)) art = P.neg ? (vowel ? "d'" : "de") : pl ? "des" : fem ? (vowel ? "de l'" : "de la") : (vowel ? "de l'" : "du");
        let s = (art.endsWith("'") ? art + noun : [art, noun].filter(Boolean).join(" ")) + (adj.length ? " " + adj.join(" ") : "");
        if (role === "to") s = art === "le" ? "au " + noun : art === "les" ? "aux " + noun : "à " + s;
        if (role === "at") s = art === "le" ? "au " + noun : "à " + s;
        if (role === "with") s = "avec " + s;
        if (role === "for") s = "pour " + s;
        return s;
      }

      const g = { der: "m", die: "f", das: "n" }[art] || "f";
      const plural = /en$|er$|s$/.test(noun) && art === "die" && n.plural;
      const caseAcc = role === "obj" || role === "for" || role === "to";
      const caseDat = role === "with" || role === "at";
      const end = (stem) => {
        if (plural) return stem + (caseDat ? "en" : "e");
        if (g === "m") return stem + (caseAcc ? "en" : caseDat ? "em" : "");
        if (g === "f") return stem + (caseDat ? "er" : "e");
        return stem + (caseDat ? "em" : "");
      };
      if (poss) art = end({ i: "mein", you: "dein", he: "sein", she: "ihr", we: "unser", they: "ihr" }[poss]);
      else if (n.det === "a" || n.det === "an") art = end("ein").replace(/^eine$/, "eine");
      else if (n.det === "this" || n.det === "that") art = { m: caseAcc ? "diesen" : caseDat ? "diesem" : "dieser", f: caseDat ? "dieser" : "diese", n: caseDat ? "diesem" : "dieses" }[g];
      else if (n.det === "the") art = { m: caseAcc ? "den" : caseDat ? "dem" : "der", f: caseDat ? "der" : "die", n: caseDat ? "dem" : "das" }[g];
      else if (n.det === "more") art = "mehr";
      else if (!n.det && MEALS[n.word]) art = "das";
      else if (!n.det) art = P && P.neg && role === "obj" ? end("kein") : "";
      const adjDe = adj.map(a => a + (art ? "en" : "es"));
      let s = [art, ...adjDe, noun].filter(Boolean).join(" ");
      if (role === "to") s = ["Laden", "Supermarkt", "Markt"].includes(noun) ? "zum " + noun : g === "f" ? "zur " + noun : "zum " + noun;
      if (role === "at") s = "bei " + s;
      if (role === "with") s = "mit " + s;
      if (role === "for") s = "für " + s;
      return s;
    }

    const tok = (hz, refs, sure = true) => hz ? { hz, rom: "", refs: [].concat(refs).filter(r => r !== undefined && r !== null), sure } : null;

    function esBuild(P, ix, person) {
      const p5 = [0, 1, 2, 3, 4, 4][person] ?? 2;
      const T = [];
      const push = (h, r, s) => { const t = tok(h, r, s); if (t) T.push(t); };
      const yesno = P.q && !P.wh;
      const whW = { what: "qué", where: (P.placeType === "to" ? "a dónde" : "dónde"), when: "cuándo", how: "cómo", why: "por qué", who: "quién", howmuch: "cuánto", howmany: "cuántos" }[P.wh];

      if (P.wh && P.wh !== "who") push((P.q ? "¿" : "") + whW, ix.wh);
      if (P.wh === "who") push("¿quién", ix.subj);
      else if (yesno) push("¿", ix.q, true);
      P.time.forEach((t, k) => { if (k === 0 && !P.wh && !P.imperative) push(TIME_X[t][3], ix["time" + k]); });
      if (P.subj && P.subj.includes(" ")) push(npEU({ det: P.subj.split(" ")[0], word: P.subj.split(" ")[1] }, "es", "subj"), ix.subj);
      else if (P.subj && ["he", "she", "they"].includes(P.subj)) push({ he: "él", she: "ella", they: "ellos" }[P.subj], ix.subj);

      let inf = P.verb ? euWord(P.verb, "es") : null;
      if (P.meal) { inf = MEALS[P.meal][0]; }
      let refl = false;
      if (inf && /se$/.test(inf) && inf.split(" ").length === 1) { refl = true; inf = inf.slice(0, -2); }
      const neg = () => { if (P.neg) push("no", ix.neg); };

      if (P.adj) {
        neg();
        const special = { hungry: "hambre", thirsty: "sed" };
        if (special[P.adj] || ((P.adj === "cold" || P.adj === "hot") && P.subj && P.subj !== "it")) {
          push(esPresent("tener", p5), ix.adj);
          push(P.degree ? "mucha " : "", ix.adj);
          push(special[P.adj] || { cold: "frío", hot: "calor" }[P.adj], ix.adj);
        } else if (WEATHER[P.adj] && (!P.subj || P.subj === "it")) {
          push("hace", ix.adj);
          push((P.degree ? "mucho " : "") + WEATHER[P.adj][0], ix.adj);
        } else {
          const cop = STATE.has(P.adj) ? "estar" : "ser";
          push(P.tense === "past" ? esPret(cop, p5) : esPresent(cop, p5), ix.adj);
          const deg = { very: "muy", so: "tan", too: "demasiado", really: "muy", "a little": "un poco" }[P.degree];
          let a = euWord(P.adj, "es") || P.adj;
          if (P.subj === "she" && /o$/.test(a)) a = a.slice(0, -1) + "a";
          push((deg ? deg + " " : "") + a, ix.adj);
        }
      } else if (P.there) {
        neg(); push("hay", ix.there); push(npEU(P.obj, "es", "obj", P), ix.obj);
      } else if (P.copula) {
        neg(); push(esPresent("ser", p5), ix.cop); push(npEU(P.obj, "es", "subj", P), ix.obj);
      } else if (inf) {
        const objPronEs = P.objPron ? { me: "me", you: "te", him: "lo", her: "la", us: "nos", them: "los", "you all": "los" }[P.objPron] : null;
        const likeV = P.verb === "like" || P.modal === "like";
        if (P.imperative && !P.neg) {
          const imp = esImperative(inf);
          push((refl || objPronEs ? esAccent(imp) : imp) + (refl ? "te" : "") + (objPronEs && !refl ? objPronEs : ""), [ix.verb, ix.objPron]);
        } else if (P.imperative && P.neg) {
          push("no", ix.neg); if (refl) push("te", ix.verb); if (objPronEs) push(objPronEs, ix.objPron); push(esSubj(inf, 1), ix.verb);
        } else if (P.lets) {
          if (inf === "ir") push("vamos", [ix.lets, ix.verb]);
          else { push("vamos a", ix.lets); push(inf + (refl ? "nos" : ""), ix.verb); }
        } else if (likeV) {
          neg();
          const obj = P.obj && P.verb === "like" && !["anything", "something"].includes(P.obj.word) ? npEU({ ...P.obj, det: P.obj.det || "the" }, "es", "subj", P) : "";
          push(esIO[p5], ix.subj ?? ix.verb);
          push((P.tense === "past" ? "gustó" : (P.obj && P.obj.plural ? "gustan" : "gusta")), ix.modal ?? ix.verb);
          if (P.verb !== "like") push(inf, ix.verb);
          if (obj) push(obj, ix.obj);
          if (P.objDem && P.objDem !== "it") push({ this: "esto", that: "eso" }[P.objDem], ix.objDem);
          if (P.really) push("mucho", ix.really);
        } else {
          neg();
          if (refl) push(esRefl[p5], ix.verb);
          if (objPronEs) push(objPronEs, ix.objPron);
          if (P.objDem === "it" && !P.modal && P.tense !== "fut") push("lo", ix.objDem);
          const modalInf = { want: "querer", can: "poder", need: "tener", should: "deber", try: "intentar" }[P.modal];
          if (modalInf) {
            push((P.tense === "past" ? esPret(modalInf, p5) : esPresent(modalInf, p5)) + (P.modal === "need" ? " que" : ""), ix.modal);
            push(inf, ix.verb);
          } else if (P.tense === "fut") {
            push(esPresent("ir", p5) + " a", ix.fut); push(inf, ix.verb);
          } else if (P.tense === "past") {
            push(esPret(inf, p5), ix.verb);
          } else if (P.prog && !P.motionProg && !P.neg) {
            const ger = { dormir: "durmiendo", leer: "leyendo", ir: "yendo", decir: "diciendo", venir: "viniendo", pedir: "pidiendo", oír: "oyendo", traer: "trayendo" }[inf] || inf.replace(/ar$/, "ando").replace(/[eií]r$/, "iendo");
            push(esPresent("estar", p5), ix.verb); push(ger, ix.verb);
          } else {
            push(esPresent(inf, p5), ix.verb);
          }
        }
        if (!likeV) {
          if (P.more && !P.obj) push("más", ix.more);
          if (P.obj && ["anything", "something"].includes(P.obj.word)) push(P.neg ? "nada" : "algo", ix.obj);
          else if (P.obj && P.obj.word === "help n") push("ayuda", ix.obj);
          else if (!P.meal) push(npEU(P.obj, "es", "obj", P), ix.obj);
          if (P.objDem && P.objDem !== "it") push({ this: "esto", that: "eso" }[P.objDem], ix.objDem);
        }
      }
      if (P.place) push(P.place.word === "where" ? "" : npEU(P.place, "es", P.placeType === "to" ? "to" : "at"), ix.place);
      if (P.withNP) push(P.withNP.pron === "me" ? "conmigo" : P.withNP.pron === "you" ? "contigo" : npEU(P.withNP, "es", "with"), ix.with);
      if (P.together) push("juntos", ix.together);
      if (P.also) push("también", ix.also);
      if (P.alot) push("mucho", ix.alot);
      if (P.yet && !P.neg) push("ya", ix.yet);
      if (P.yet && P.neg) { const k = T.findIndex(t => t.hz === "no"); if (k >= 0) T[k].hz = "todavía no"; }
      if (P.well) push("bien", ix.verb);
      P.time.forEach((t, k) => { if (k > 0 || P.wh || P.imperative) push(TIME_X[t][3], ix["time" + k]); });
      if (P.please) push("por favor", ix.please);
      fixPunct(T, P, "es");
      return T;
    }


    /* ---------- French ---------- */

    function frBuild(P, ix, person) {
      const p6 = person;
      const T = [];
      const push = (h, r, s) => { const t = tok(h, r, s); if (t) T.push(t); };
      const yesno = P.q && !P.wh;
      const whEnd = { what: "quoi", where: "où", when: "quand", howmuch: "combien", howmany: "combien" }[P.wh];
      const whFront = { how: "comment", why: "pourquoi" }[P.wh];

      if (whFront) push(whFront.charAt(0).toUpperCase() + whFront.slice(1), ix.wh);
      if (P.wh === "who") push("Qui", ix.subj);

      let subj = P.subj === "who" ? null : P.subj ? (P.subj.includes(" ") ? npEU({ det: P.subj.split(" ")[0], word: P.subj.split(" ")[1] }, "fr", "subj") : { i: "je", you: "tu", he: "il", she: "elle", it: "ça", we: "on", "you all": "vous", they: "ils", everyone: "tout le monde" }[P.subj]) : null;
      const pi = P.subj === "we" || P.subj === "everyone" || P.subj === "it" ? 2 : P.subj === "who" ? 2 : P.subj && P.subj.includes(" ") ? 2 : p6 === 3 ? 2 : p6;

      let inf = P.verb ? euWord(P.verb, "fr") : null;
      if (P.meal) inf = MEALS[P.meal][1];
      if ((P.verb === "go" || P.verb === "come") && P.place && P.place.word === "home") { inf = "rentrer"; }
      if (P.verb === "cook" && P.obj) inf = "préparer";
      if (inf === "manquer" && P.objPron && !P.imperative && !P.lets) {
        const s2 = { me: "je", you: "tu", him: "il", her: "elle", us: "on", them: "ils" }[P.objPron];
        const cl = { i: "me", you: "te", he: "lui", she: "lui", we: "nous", they: "leur", "you all": "vous" }[P.subj] || "me";
        const pp = { je: 0, tu: 1, il: 2, elle: 3, on: 2, ils: 5 }[s2];
        const parts = [];
        if (P.neg) parts.push(s2, "ne", cl, frPresent("manquer", pp), "pas"); else parts.push(s2, cl, frPresent("manquer", pp));
        push(parts.join(" ").replace(/^je /, "je ").replace(/ ne (me|te)/, " ne $1"), [ix.subj, ix.verb, ix.objPron, ix.neg].filter(x => x !== undefined));
        if (P.alot) push("beaucoup", ix.alot);
        P.time.forEach((t, k) => push(TIME_X[t][4], ix["time" + k]));
        fixPunct(T, P, "fr");
        return T;
      }
      let refl = false;
      if (inf && /^(se |s')/.test(inf)) { refl = true; inf = inf.replace(/^se |^s'/, ""); if (inf === "asseoir") inf = "s'asseoir"; if (inf === "souvenir") inf = "se souvenir"; }
      let extra = "";
      if (inf && inf.includes(" ") && !FR_IRR[inf]) { const pts = inf.split(" "); inf = pts[0]; extra = pts.slice(1).join(" "); }

      const subjTok = (verb) => {
        if (!subj) return;
        if (subj === "je" && elide(verb)) push("j'" + verb.replace(/^/, ""), ix.subj);
        else push(subj, ix.subj);
      };

      const verbGroup = (fin, ref, rest) => {
        const reflP = refl ? frRefl[pi] : "";
        let first = (reflP ? (elide(fin) ? reflP.slice(0, -1) + "'" : reflP + " ") : "") + fin;
        if (P.neg) first = (elide(first) ? "n'" : "ne ") + first + " pas";
        if (subj === "je" && elide(first)) { push("j'" + first, [ix.subj, ref].filter(x => x !== undefined)); }
        else { if (subj) push(subj, ix.subj); push(first, ref); }
        if (rest) push(rest, ix.verb);
      };

      if (P.adj) {
        const special = { hungry: "faim", thirsty: "soif" };
        if (special[P.adj] || ((P.adj === "cold" || P.adj === "hot") && P.subj && P.subj !== "it")) {
          verbGroup(frPresent("avoir", pi), ix.adj); push((P.degree ? "très " : "") + (special[P.adj] || { cold: "froid", hot: "chaud" }[P.adj]), ix.adj);
        } else if (WEATHER[P.adj] && (!P.subj || P.subj === "it")) {
          subj = "il"; verbGroup("fait", ix.adj); push((P.degree ? "très " : "") + WEATHER[P.adj][1], ix.adj);
        } else {
          const deg = { very: "très", so: "tellement", too: "trop", really: "vraiment", "a little": "un peu" }[P.degree];
          let a = euWord(P.adj, "fr") || P.adj;
          if (P.subj === "she" && !/e$/.test(a)) a += "e";
          if ((!subj || P.subj === "it") && !P.imperative) { push(P.neg ? (P.yet ? "Ce n'est pas encore" : "Ce n'est pas") : "C'est", [ix.adj, ix.neg].filter(x => x !== undefined)); push((deg ? deg + " " : "") + a, ix.adj); }
          else if (P.imperative) { push(P.neg ? "Ne sois pas" : "Sois", ix.adj); push(a, ix.adj); }
          else {
            if (P.tense === "past") { verbGroup(frPresent("avoir", pi), ix.adj, "été"); }
            else verbGroup(frPresent("être", pi), ix.adj);
            push((deg ? deg + " " : "") + a, ix.adj);
          }
        }
      } else if (P.there) {
        push(P.neg ? "Il n'y a pas" : "Il y a", ix.there); push(npEU(P.obj, "fr", "obj", P), ix.obj);
      } else if (P.copula) {
        if (!subj) { push(P.neg ? "Ce n'est pas" : "C'est", ix.cop); }
        else verbGroup(frPresent("être", pi), ix.cop);
        push(npEU(P.obj, "fr", "subj", P), ix.obj);
      } else if (inf) {
        const objPronFr = P.objPron ? { me: "me", you: "te", him: "le", her: "la", us: "nous", them: "les", "you all": "vous" }[P.objPron] : null;
        if (P.imperative) {
          const imp = frImperative(inf);
          if (P.neg) { const lead = (refl ? "te " : "") + (objPronFr ? objPronFr + " " : "") + imp; push((elide(lead) ? "N'" : "Ne ") + lead + " pas", ix.verb); }
          else push(imp.charAt(0).toUpperCase() + imp.slice(1) + (refl ? "-toi" : "") + (objPronFr ? "-" + ({ me: "moi", te: "toi" }[objPronFr] || objPronFr) : ""), ix.verb);
          if (extra) push(extra, ix.verb);
        } else if (P.lets) {
          push(frNous(inf).charAt(0).toUpperCase() + frNous(inf).slice(1) + (refl ? "-nous" : ""), [ix.lets, ix.verb]);
          if (extra) push(extra, ix.verb);
        } else {
          const objLead = objPronFr ? (elide(inf) ? objPronFr.slice(0, -1) + "'" : objPronFr + " ") : "";
          const modalInf = { want: "vouloir", can: "pouvoir", need: "devoir", should: "devoir", like: "aimer", try: "essayer" }[P.modal];
          if (modalInf) {
            const fin = P.tense === "past" ? frPresent("avoir", pi) : frPresent(modalInf, pi);
            if (P.tense === "past") verbGroup(fin, ix.modal, frPP(modalInf)); else verbGroup(P.modal === "should" ? frPresent("devoir", pi).replace(/s$|t$/, m => m) : fin, ix.modal);
            push((P.modal === "try" ? "de " : "") + objLead + (refl ? frRefl[pi] + " " : "") + inf.replace(/^s'|^se /, ""), ix.verb);
          } else if (P.tense === "fut") {
            verbGroup(frPresent("aller", pi), ix.fut);
            push(objLead + (refl ? frRefl[pi] + " " : "") + inf.replace(/^s'|^se /, ""), ix.verb);
          } else if (P.tense === "past") {
            const etre = FR_ETRE.has(inf) || refl;
            let pp = frPP(inf);
            if (etre && (P.subj === "we" || P.subj === "they" || P.subj === "you all")) pp += "s";
            if (etre && P.subj === "she") pp += "e";
            const auxF = etre ? frPresent("être", pi) : frPresent("avoir", pi);
            verbGroup((objLead) + auxF, ix.verb, (P.well ? "bien " : "") + pp);
          } else {
            verbGroup(objLead + frPresent(inf, pi), ix.verb);
          }
          if (extra) push(extra, ix.verb);
        }
        if (P.more && !P.obj) push("plus", ix.more);
        if (P.really) push("vraiment", ix.really);
        if (P.objDem) push("ça", ix.objDem);
        if (P.obj && ["anything", "something"].includes(P.obj.word)) { if (P.neg) { const k = T.findIndex(t => / pas$/.test(t.hz)); if (k >= 0) T[k].hz = T[k].hz.replace(/ pas$/, ""); } push(inf === "avoir" && extra === "besoin" ? (P.neg ? "de rien" : "de quelque chose") : (P.neg ? "rien" : "quelque chose"), ix.obj); }
        else if (P.obj && P.obj.word === "help n") push("d'aide", ix.obj);
        else if (!P.meal) push(npEU(P.obj, "fr", "obj", P), ix.obj);
      }
      if (P.place && P.place.word !== "where" && inf !== "rentrer") push(npEU(P.place, "fr", P.placeType === "to" ? "to" : "at"), ix.place);
      if (P.withNP) push(npEU(P.withNP, "fr", "with"), ix.with);
      if (P.together) push("ensemble", ix.together);
      if (P.also) push("aussi", ix.also);
      if (P.alot) push("beaucoup", ix.alot);
      if (P.yet && !P.neg) push("déjà", ix.yet);
      if (whEnd) push(whEnd, ix.wh);
      P.time.forEach((t, k) => push(TIME_X[t][4], ix["time" + k]));
      if (P.please) push(P.subj === "you all" ? "s'il vous plaît" : "s'il te plaît", ix.please);
      if (T[0] && /^[a-zàâéèêç]/.test(T[0].hz)) T[0].hz = T[0].hz.charAt(0).toUpperCase() + T[0].hz.slice(1);
      fixPunct(T, P, "fr");
      return T;
    }


    /* ---------- German ---------- */

    function deBuild(P, ix, person) {
      const T = [];
      const push = (h, r, s) => { const t = tok(h, r, s); if (t) T.push(t); };
      const yesno = P.q && !P.wh;
      const pi = P.subj === "who" ? 2 : P.subj && P.subj.includes(" ") && P.subj !== "you all" ? 2 : P.subj === "everyone" ? 5 : person;
      const subj = P.subj === "who" ? "wer" : P.subj ? (P.subj.includes(" ") ? npEU({ det: P.subj.split(" ")[0], word: P.subj.split(" ")[1] }, "de", "subj") : { i: "ich", you: "du", he: "er", she: "sie", it: "es", we: "wir", "you all": "ihr", they: "sie", everyone: "alle" }[P.subj]) : null;
      const wh = { what: "was", where: P.placeType === "to" ? "wohin" : "wo", when: "wann", how: "wie", why: "warum", howmuch: "wie viel", howmany: "wie viele" }[P.wh];

      let finite = null, finRef = null, tail = [], mid = [];
      let inf = P.verb ? euWord(P.verb, "de") : null;
      if (P.meal) inf = MEALS[P.meal][2];
      let sp = inf ? deSplit(inf) : null;
      const reflP = ["mich", "dich", "sich", "uns", "euch", "sich", "sich"];

      if (P.adj) {
        const special = { hungry: "Hunger", thirsty: "Durst" };
        if (special[P.adj]) { finite = dePresent("haben", pi); finRef = ix.adj; mid.push([special[P.adj], ix.adj]); if (P.neg) mid.unshift(["keinen", ix.neg]); }
        else if ((P.adj === "cold" || P.adj === "hot") && P.subj && P.subj !== "it") {
          finite = "ist"; finRef = ix.adj;
          const dat = { i: "mir", you: "dir", he: "ihm", she: "ihr", we: "uns", "you all": "euch", they: "ihnen" }[P.subj] || "mir";
          return deOrder(T, push, P, ix, wh, "es".replace("es", ""), finite, finRef, [[dat, ix.subj], ...(P.neg ? [["nicht", ix.neg]] : []), [{ cold: "kalt", hot: "heiß" }[P.adj], ix.adj]], [], yesno, true);
        } else {
          finite = P.tense === "past" ? (["war", "warst", "war", "waren", "wart", "waren", "waren"][pi]) : dePresent("sein", pi); finRef = ix.adj;
          const deg = { very: "sehr", so: "so", too: "zu", really: "echt", "a little": "ein bisschen" }[P.degree];
          if (P.neg) mid.push([P.yet ? "noch nicht" : "nicht", ix.neg]);
          mid.push([(deg ? deg + " " : "") + (euWord(P.adj, "de") || P.adj), ix.adj]);
          if (!subj && !P.imperative) return deOrder(T, push, P, ix, wh, "es", finite, finRef, mid, tail, yesno);
        }
      } else if (P.there) {
        finite = "gibt"; finRef = ix.there;
        return deOrder(T, push, P, ix, wh, "es", finite, finRef, [[npEU(P.obj, "de", "obj", { ...P }), ix.obj]], [], yesno);
      } else if (P.copula) {
        finite = dePresent("sein", pi); finRef = ix.cop;
        if (P.neg) mid.push(["nicht", ix.neg]);
        mid.push([npEU(P.obj, "de", "subj"), ix.obj]);
        if (!subj) return deOrder(T, push, P, ix, wh, "das", finite, finRef, mid, tail, yesno);
      } else if (sp) {
        const objPronDe = P.objPron ? ({ call: 1, see: 1, visit: 1, love: 1, miss: 1, like: 1, meet: 1 }[P.verb] ? { me: "mich", you: "dich", him: "ihn", her: "sie", us: "uns", them: "sie", "you all": "euch" } : { me: "mir", you: "dir", him: "ihm", her: "ihr", us: "uns", them: "ihnen", "you all": "euch" })[P.objPron] : null;
        const modalInf = { want: "wollen", can: "können", need: "müssen", should: "sollen", like: null, try: null }[P.modal];
        const fullInf = sp.pre + sp.v;
        if (sp.refl) mid.push([reflP[pi], ix.verb]);
        if (objPronDe) mid.push([objPronDe, ix.objPron]);
        if (P.imperative) {
          finite = deImperative(sp.v); finRef = ix.verb;
          const objS = npEU(P.obj, "de", "obj", P);
          const parts = [];
          if (sp.refl) parts.push(["dich", ix.verb]);
          if (objPronDe) parts.push([objPronDe, ix.objPron]);
          if (objS) parts.push([objS, ix.obj]);
          if (sp.before) parts.push([sp.before, ix.verb]);
          if (P.neg) parts.push(["nicht", ix.neg]);
          if (sp.pre) parts.push([sp.pre, ix.verb]);
          push(finite.charAt(0).toUpperCase() + finite.slice(1), ix.verb);
          const pre = parts.filter(x => x[0] === sp.pre && sp.pre);
          const rest = parts.filter(x => !(x[0] === sp.pre && sp.pre));
          const lead = rest.filter(x => x[1] === ix.objPron || x[0] === "dich");
          const body = rest.filter(x => !(x[1] === ix.objPron || x[0] === "dich"));
          lead.forEach(([h, r]) => push(h, r));
          if (P.please) push("bitte", ix.please);
          addTailDe(push, P, ix);
          body.forEach(([h, r]) => push(h, r));
          pre.forEach(([h, r]) => push(h, r));
          fixPunct(T, P, "de");
          return T;
        }
        if (P.lets) {
          push("Lass", ix.lets); push("uns", ix.lets);
          const objS = npEU(P.obj, "de", "obj", P);
          if (objS) push(objS, ix.obj);
          addTailDe(push, P, ix);
          if (sp.before) push(sp.before, ix.verb);
          push(fullInf, ix.verb);
          fixPunct(T, P, "de");
          return T;
        }
        if (P.modal === "like" || (P.verb === "like" && !P.obj)) {
          finite = dePresent(sp.v === "mögen" ? "mögen" : sp.v, pi); finRef = ix.verb;
          if (sp.v !== "mögen") tail.push(["gern", ix.modal]);
        } else if (modalInf) {
          finite = P.tense === "past" ? null : dePresent(modalInf, pi); finRef = ix.modal;
          if (P.tense === "past") { finite = ["wollte", "wolltest", "wollte", "wollten", "wolltet", "wollten", "wollten"][pi]; if (modalInf === "können") finite = ["konnte", "konntest", "konnte", "konnten", "konntet", "konnten", "konnten"][pi]; if (modalInf === "müssen") finite = ["musste", "musstest", "musste", "mussten", "musstet", "mussten", "mussten"][pi]; }
          tail.push([(sp.before ? sp.before + " " : "") + fullInf, ix.verb]);
        } else if (P.tense === "fut") {
          finite = dePresent("werden", pi); finRef = ix.fut;
          tail.push([(sp.before ? sp.before + " " : "") + fullInf, ix.verb]);
        } else if (P.tense === "past") {
          const sein = DE_SEIN.has(fullInf) || DE_SEIN.has(sp.v);
          finite = dePresent(sein ? "sein" : "haben", pi); finRef = ix.verb;
          tail.push([(sp.before ? sp.before + " " : "") + dePP(sp.v, sp.pre), ix.verb]);
        } else {
          finite = dePresent(sp.v, pi); finRef = ix.verb;
          if (sp.before) tail.push([sp.before, ix.verb]);
          if (sp.pre) tail.push([sp.pre, ix.verb]);
        }
        const objS = P.meal ? "" : P.obj && ["anything", "something"].includes(P.obj.word) ? (P.neg ? "nichts" : "etwas") : P.obj && P.obj.word === "help n" ? "Hilfe" : npEU(P.obj, "de", "obj", P);
        if (P.objDem) mid.push([{ it: "es", this: "das", that: "das" }[P.objDem], ix.objDem]);
        if (P.really) mid.push(["wirklich", ix.really]);
        if (P.prog && !P.motionProg && !P.neg && P.tense === "pres" && !P.modal) mid.push(["gerade", ix.verb]);
        if (objS) mid.push([objS, ix.obj]);
        if (P.more && !P.obj) mid.push(["mehr", ix.more]);
        if (P.neg && !(objS && /^(kein|nichts)/.test(objS))) tail.unshift([P.yet ? "noch nicht" : P.well ? "nicht gut" : "nicht", ix.neg]);
      } else return [];

      return deOrder(T, push, P, ix, wh, subj, finite, finRef, mid, tail, yesno);
    }

    function addTailDe(push, P, ix) {
      P.time.forEach((t, k) => push(TIME_X[t][5], ix["time" + k]));
      if (P.together) push("zusammen", ix.together);
      if (P.also) push("auch", ix.also);
      if (P.alot) push("viel", ix.alot);
      if (P.withNP) push(npEU(P.withNP, "de", "with"), ix.with);
      if (P.place && P.place.word !== "where") push(npEU(P.place, "de", P.placeType === "to" ? "to" : "at"), ix.place);
    }

    function deOrder(T, push, P, ix, wh, subj, finite, finRef, mid, tail, yesno, noSubj) {
      const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
      if (wh) {
        push(cap(wh), ix.wh ?? ix.subj);
        push(finite, finRef);
        if (subj && subj !== "wer") push(subj, ix.subj);
      } else if (yesno) {
        push(cap(finite), finRef);
        if (subj) push(subj, ix.subj);
      } else if (subj && !noSubj) {
        push(cap(subj), ix.subj);
        push(finite, finRef);
      } else {
        push(cap(finite), finRef);
      }
      if (P.time.length) P.time.forEach((t, k) => push(TIME_X[t][5], ix["time" + k]));
      if (P.also) push("auch", ix.also);
      if (P.yet && !P.neg) push("schon", ix.yet);
      if (P.well && !P.neg) push("gut", ix.verb);
      if (P.together) push("zusammen", ix.together);
      mid.forEach(([h, r]) => push(h, r));
      if (P.withNP) push(npEU(P.withNP, "de", "with"), ix.with);
      if (P.alot) push("viel", ix.alot);
      const hasPlace = P.place && P.place.word !== "where";
      if (hasPlace && tail.length && tail[0][0] === "nicht") push(tail.shift()[0], ix.neg);
      if (hasPlace) push(npEU(P.place, "de", P.placeType === "to" ? "to" : "at"), ix.place);
      tail.forEach(([h, r]) => push(h, r));
      if (P.please) push("bitte", ix.please);
      fixPunct(T, P, "de");
      return T;
    }

    function fixPunct(T, P, lang) {
      const clean = T.filter(t => t.hz);
      T.length = 0;
      clean.forEach(t => T.push(t));
      if (!T.length) return;
      const last = T[T.length - 1];
      if (P.q) last.hz += "?";
      if (lang === "es") {
        if (T[0].hz === "¿" && T[1]) { T[1].hz = "¿" + T[1].hz; T[1].refs = T[1].refs.concat(T[0].refs); T.shift(); }
        const first = T[0];
        first.hz = first.hz.replace(/^(¿?)(.)/, (m, a, b) => a + b.toUpperCase());
        if (P.imperative && P.neg) first.hz = first.hz.replace(/^no/, "No");
      } else {
        T[0].hz = T[0].hz.charAt(0).toUpperCase() + T[0].hz.slice(1);
      }
    }


    /* ---------- entry ---------- */

    const SPECIAL = {
      "how are you": [["你好嗎", "nei5 hou2 maa3"], ["你好吗", "nǐ hǎo ma"], ["你好嗎", "ni33 hɔu55 ma33", false], "¿Cómo estás?", "Comment ça va?", "Wie geht's dir?", ["How", "are you"]],
      "how is it going": [["點呀", "dim2 aa3"], ["怎么样", "zěn me yàng"], ["幾何啊", "gi55 hɔu215 a33"], "¿Cómo va todo?", "Ça va?", "Wie läuft's?", ["How", "is it going"]],
      "thank you": [["多謝", "do1 ze6"], ["谢谢", "xiè xie"], ["多謝", "ɔ33 de32"], "Gracias", "Merci", "Danke", ["Thank you"]],
      "thank you so much": [["多謝晒", "do1 ze6 saai3"], ["太谢谢你了", "tài xiè xie nǐ le"], ["多謝晒", "ɔ33 de32 sai33", false], "Muchas gracias", "Merci beaucoup", "Vielen Dank", ["Thank you", "so much"]],
      "i love you": [["我愛你", "ngo5 oi3 nei5"], ["我爱你", "wǒ ài nǐ"], ["我愛你", "ŋɔi33 ɔi33 ni33", false], "Te quiero", "Je t'aime", "Ich liebe dich", ["I", "love", "you"]],
      "i love you all": [["我好錫你哋", "ngo5 hou2 sek3 nei5 dei6"], ["我爱你们", "wǒ ài nǐ men"], ["我好錫你", "ŋɔi33 hɔu55 ɬɛk33 ni21", false], "Los quiero mucho", "Je vous aime", "Ich hab euch lieb", ["I", "love", "you all"]],
      "what is your name": [["你叫乜嘢名呀", "nei5 giu3 mat1 je5 meng2 aa3"], ["你叫什么名字", "nǐ jiào shén me míng zi"], ["你估乜名啊", "ni33 gu55 mɔt55 miaŋ22 a33"], "¿Cómo te llamas?", "Comment tu t'appelles?", "Wie heißt du?", ["What", "is", "your name"]],
      "why not": [["點解唔得", "dim2 gaai2 m4 dak1"], ["为什么不呢", "wèi shén me bù ne"], ["做乜唔得", "du33 mɔt55 m22 ak55", false], "¿Por qué no?", "Pourquoi pas?", "Warum nicht?", ["Why", "not"]],
      "how much is it": [["幾多錢呀", "gei2 do1 cin2 aa3"], ["多少钱", "duō shao qián"], ["幾多錢啊", "gi55 ɔ335 tein225 a33", false], "¿Cuánto cuesta?", "C'est combien?", "Wie viel kostet das?", ["How much", "is it"]],
      "how many people": [["有幾多人呀", "jau5 gei2 do1 jan4 aa3"], ["几个人", "jǐ ge rén"], ["有幾多人啊", "yiu33 gi55 ɔ335 ŋin22 a33", false], "¿Cuántas personas?", "Combien de personnes?", "Wie viele Leute?", ["How many", "people"]],
      "excuse me": [["唔好意思", "m4 hou2 ji3 si1"], ["不好意思", "bù hǎo yì si"], ["唔好意思", "m22 hɔu55 yi33 ɬu55", false], "Disculpa", "Excuse-moi", "Entschuldigung", ["Excuse me"]],
    };

    function special(text) {
      const k = expand(text).join(" ").replace(/you guys|y'all/g, "you all");
      const S = SPECIAL[k];
      const m = k.match(/^thank you (?:so much )?for (?:the |your |my )?(.+)$/);
      if (!S && m) {
        const noun = lemmas(m[1]).find(l => LEX[l] || CORE[l]);
        if (!noun) return null;
        const z = zhWord(noun);
        const n = { word: noun, det: "the" };
        const es = npEU(n, "es", "subj"), fr = npEU(n, "fr", "subj"), de = npEU(n, "de", "for");
        if (!z || !es) return null;
        const zh = (L, a, b) => [{ hz: a[0], rom: a[1], refs: [0], sure: a[2] !== false }, { hz: b[0], rom: b[1], refs: [1], sure: b[2] !== false }, ...(z[L] ? [{ hz: z[L][0], rom: z[L][1], refs: [2], sure: z[L][2] !== false }] : [])];
        return { gloss: ["Thank you", "for", "the " + noun], yue: zh("yue", ["多謝", "do1 ze6"], ["你嘅", "nei5 ge3"]), cmn: zh("cmn", ["谢谢", "xiè xie"], ["你的", "nǐ de"]), tsn: zh("tsn", ["多謝", "ɔ33 de32"], ["你個", "ni33 gɔi33", false]),
          es: [{ hz: "Gracias", rom: "", refs: [0] }, { hz: "por " + es, rom: "", refs: [1, 2] }], fr: [{ hz: "Merci", rom: "", refs: [0] }, { hz: "pour " + fr, rom: "", refs: [1, 2] }], de: [{ hz: "Danke", rom: "", refs: [0] }, { hz: de, rom: "", refs: [1, 2] }] };
      }
      if (!S) return null;
      const all = S[6].map((_, i) => i);
      const zh = x => [{ hz: x[0], rom: x[1], refs: all, sure: x[2] !== false }];
      const eu = x => [{ hz: x, rom: "", refs: all }];
      return { gloss: S[6], yue: zh(S[0]), cmn: zh(S[1]), tsn: zh(S[2]), es: eu(S[3]), fr: eu(S[4]), de: eu(S[5]) };
    }

    function whBe(text, P) {
      const n = P.whBe;
      const z = zhWord(n.word);
      if (!z) return null;
      const subj = { es: npEU({ ...n, det: n.det || "the" }, "es", "subj"), fr: npEU({ ...n, det: n.det || "the" }, "fr", "subj"), de: npEU({ ...n, det: n.det || "the" }, "de", "subj") };
      const plural = n.plural || /^(los|las|les) /.test(subj.es);
      const whG = { where: "where", what: "what", who: "who", how: "how" }[P.wh];
      if (!whG) return null;
      const gloss = [whG.charAt(0).toUpperCase() + whG.slice(1), "is", (n.det && n.det !== "the" ? n.det + " " : "the ") + n.word];
      const Z = {
        where: { yue: [["喺", "hai2"], ["邊度呀", "bin1 dou6 aa3"]], cmn: [["在", "zài"], ["哪里", "nǎ li"]], tsn: [["喺", "hai55", false], ["哪啊", "nai215 a33"]] },
        what: { yue: [["係", "hai6"], ["乜嘢呀", "mat1 je5 aa3"]], cmn: [["是", "shì"], ["什么", "shén me"]], tsn: [["係", "hai32"], ["乜嘢啊", "mɔt55 yia33 a33"]] },
        who: { yue: [["係", "hai6"], ["邊個呀", "bin1 go3 aa3"]], cmn: [["是", "shì"], ["谁", "shéi"]], tsn: [["係", "hai32"], ["谁啊", "sui55 a33"]] },
        how: { yue: [["", ""], ["點呀", "dim2 aa3"]], cmn: [["", ""], ["怎么样", "zěn me yàng"]], tsn: [["", ""], ["幾何啊", "gi55 hɔu215 a33"]] },
      }[P.wh];
      const owner = n.det && POSS[n.det];
      const zh = L => {
        const t = [];
        if (owner) { const o = zhWord(owner); t.push({ hz: o[L][0] + (KIN.has(n.word) ? "" : { yue: "嘅", cmn: "的", tsn: "個" }[L]), rom: o[L][1] + (KIN.has(n.word) ? "" : { yue: " ge3", cmn: " de", tsn: " gɔi33" }[L]), refs: [2], sure: true }); }
        if (z[L]) t.push({ hz: z[L][0], rom: z[L][1], refs: [2], sure: z[L][2] !== false });
        const [a, b] = Z[L];
        if (a[0]) t.push({ hz: a[0], rom: a[1], refs: [1], sure: a[2] !== false });
        t.push({ hz: b[0], rom: b[1], refs: [0], sure: b[2] !== false });
        return t;
      };
      const tk = (h, r) => ({ hz: h, rom: "", refs: r });
      const es = { where: [tk("¿Dónde", [0]), tk(plural ? "están" : "está", [1]), tk(subj.es + "?", [2])], what: [tk("¿Qué", [0]), tk(plural ? "son" : "es", [1]), tk(subj.es + "?", [2])], who: [tk("¿Quién", [0]), tk("es", [1]), tk(subj.es + "?", [2])], how: [tk("¿Cómo", [0]), tk(plural ? "están" : "está", [1]), tk(subj.es + "?", [2])] }[P.wh];
      const plFr = n.plural || /^(les|mes|tes|ses|nos|vos|leurs) /.test(subj.fr);
      const fr = { where: [tk("Où", [0]), tk(plFr ? "sont" : "est", [1]), tk(subj.fr + "?", [2])], what: [tk("C'est", [1]), tk("quoi,", [0]), tk(subj.fr + "?", [2])], who: [tk("Qui", [0]), tk("est", [1]), tk(subj.fr + "?", [2])], how: [tk("Comment", [0]), tk(plFr ? "vont" : "va", [1]), tk(subj.fr + "?", [2])] }[P.wh];
      const de = { where: [tk("Wo", [0]), tk(plural ? "sind" : "ist", [1]), tk(subj.de + "?", [2])], what: [tk("Was", [0]), tk("ist", [1]), tk(subj.de + "?", [2])], who: [tk("Wer", [0]), tk("ist", [1]), tk(subj.de + "?", [2])], how: [tk("Wie", [0]), tk(plural ? "sind" : "ist", [1]), tk(subj.de + "?", [2])] }[P.wh];
      const p = { en: text, gloss, yue: zh("yue"), cmn: zh("cmn"), tsn: zh("tsn"), es, fr, de, guess: true, composed: true, tip: tr("c_note") };
      return { p, found: 3, counted: 3 };
    }


    function compose(text) {
      const sp = special(text);
      if (sp) {
        return { p: { en: text, ...sp, guess: true, composed: true, tip: tr("c_note") }, found: sp.gloss.length, counted: sp.gloss.length };
      }
      const P = parse(text);
      if (!P) return null;
      if (P.whBe) return whBe(text, P);
      let B;
      try { B = build(P); } catch (e) { return null; }
      if (!B.yue.length || !B.es.length) return null;
      const out = { en: text, gloss: B.gloss, yue: B.yue, cmn: B.cmn.filter(t => t.hz), tsn: B.tsn, es: B.es, fr: B.fr, de: B.de, guess: true, composed: true };
      const notes = [tr("c_note")];
      if (B.miss) notes.push(tr("b_missing"));
      out.tip = notes.join(" ");
      return { p: out, found: B.gloss.length - B.miss, counted: B.gloss.length, parse: P };
    }

    return { compose, parse };
  })();
