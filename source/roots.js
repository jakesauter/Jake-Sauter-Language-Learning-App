  /* rules and roots: character parts, sound families, sound shifts between languages, and each language's "axioms" */

  const RAD = {
    "亻": ["person", "你他們住休做使信借估位份低便傾伴伯何"],
    "氵": ["water", "洗游海湯河酒沖淋清溫滾漂沙汁油泳渴湖汽浸洋淨滑漏江浪"],
    "冫": ["ice", "冷凍冰"],
    "忄": ["heart, feeling", "忙快慢怕情性惜懂"],
    "心": ["heart, mind", "想念忘愛感意思急怒您悶"],
    "口": ["mouth, a spoken word", "吃喝叫唱吹咩嘅嘢咗唔嚟啦呀嗎吧呢哋喺噉咁啲嗰咪吓"],
    "扌": ["hand", "打搵揸推拉抱把摸找接提掃拎擺換掛揀撳搬抄拍指"],
    "目": ["eye", "睇瞓眼睛睡看眉盲瞌"],
    "艹": ["plant", "茶菜花草葉蘋藥蔥薑菇"],
    "宀": ["roof", "家安室客宿寫富寶寒定"],
    "飠": ["food", "飯飲餓飽餅館餸餃"],
    "訁": ["speech", "話說講語請謝讀認識記試誰課該詞譯談"],
    "木": ["tree, wood", "林森樹椅枱桌板校橋杯枕檸樓機根"],
    "日": ["sun, time", "早晚時明星昨晨晴暖曬暗春"],
    "辶": ["walking, movement", "這返過進遠近送道邊還逛迎追遊達通"],
    "女": ["woman", "媽姐妹奶婆姑嫂好她妻婚姓娘嫲"],
    "足": ["foot", "跑跳路踢跟跌"],
    "火": ["fire, cooking", "炒燒煮煲爐熱燈煙炸炮焗熟煎"],
    "釒": ["metal", "錢鐘錶鎖鑰銀鐵針鍋銅"],
    "月": ["body (this 月 was 肉, flesh)", "肚腳腦胸肩背臉胖肥腿膊"],
    "糸": ["thread, silk", "紅綠紙線細結紹給"],
    "疒": ["sickness", "病痛瘦疲"],
    "雨": ["weather", "雪雲電雷霧露"],
    "衤": ["clothing", "衫褲襪被裙"],
    "犭": ["animal", "狗狼獅猴狐"],
    "貝": ["shell, money (shells were money)", "買賣貴貨費財賺"],
    "石": ["stone", "碗碟破硬碰"],
    "子": ["child", "孩孫學字"],
    "門": ["door", "開閂間閒關"],
  };

  const PHON = {
    "馬": ["maa5", "mǎ", "媽嗎罵碼"],
    "羊": ["joeng4", "yáng", "洋樣養氧"],
    "青": ["cing1", "qīng", "請清情晴睛精靜"],
    "包": ["baau1", "bāo", "飽抱跑泡炮胞"],
    "方": ["fong1", "fāng", "房放訪芳防"],
    "工": ["gung1", "gōng", "紅空江功攻"],
    "巴": ["baa1", "bā", "爸吧把爬"],
    "主": ["zyu2", "zhǔ", "住注柱"],
    "古": ["gu2", "gǔ", "姑苦故估固"],
    "交": ["gaau1", "jiāo", "校較餃咬郊膠"],
    "化": ["faa3", "huà", "花貨"],
    "反": ["faan2", "fǎn", "飯返板版"],
    "生": ["saang1", "shēng", "星姓性"],
    "果": ["gwo2", "guǒ", "課顆"],
    "門": ["mun4", "mén", "們問聞悶"],
    "可": ["ho2", "kě", "哥河歌何"],
    "白": ["baak6", "bái", "伯拍怕百"],
    "長": ["coeng4", "cháng", "張帳"],
    "尚": ["soeng6", "shàng", "常堂嘗"],
    "弟": ["dai6", "dì", "第梯"],
    "曷": ["hot3", "hé", "喝渴"],
    "艮": ["gan3", "gèn", "很跟根銀眼"],
    "中": ["zung1", "zhōng", "種仲"],
    "分": ["fan1", "fēn", "份粉"],
    "半": ["bun3", "bàn", "伴拌胖"],
    "加": ["gaa1", "jiā", "架咖"],
    "胡": ["wu4", "hú", "湖糊蝴"],
    "令": ["ling6", "lìng", "冷鈴零領"],
    "良": ["loeng4", "liáng", "娘浪狼"],
    "同": ["tung4", "tóng", "銅筒洞"],
    "里": ["lei5", "lǐ", "理裡"],
    "甬": ["jung2", "yǒng", "通痛桶"],
    "既": ["gei3", "jì", "嘅"],
    "左": ["zo2", "zuǒ", "咗"],
    "黎": ["lai4", "lí", "嚟"],
    "係": ["hai6", "xì", "喺"],
    "野": ["je5", "yě", "嘢"],
    "地": ["dei6", "dì", "哋"],
    "甘": ["gam1", "gān", "咁"],
    "個": ["go3", "gè", "嗰"],
    "的": ["dik1", "de", "啲"],
    "吾": ["ng4", "wú", "唔"],
  };

  const RAD_OF = {};
  Object.entries(RAD).forEach(([r, [m, chars]]) => [...chars].forEach(c => { RAD_OF[c] = r; }));
  const PHON_OF = {};
  Object.entries(PHON).forEach(([k, v]) => [...v[2]].forEach(c => { PHON_OF[c] = k; }));

  function charRule(c) {
    const r = RAD_OF[c], ph = PHON_OF[c];
    if (c === "咩") return "咩 = 口 (a spoken word) + 羊 (sheep): sheep say \"meh\". 咩 me1 means what?";
    if (r && ph) return `${c} = ${r} (${RAD[r][0]}, the meaning) + ${ph} (${PHON[ph][0]} / ${PHON[ph][1]}, a sound hint). About 80% of characters are built this way.`;
    if (ph) return `${c} gets a sound hint from ${ph} (${PHON[ph][0]} / ${PHON[ph][1]}). Others in the family: ${[...PHON[ph][2]].filter(x => x !== c).slice(0, 4).join(" ")}.`;
    if (r) return `${c} has ${r} (${RAD[r][0]}). Others with it: ${[...RAD[r][1]].filter(x => x !== c).slice(0, 5).join(" ")}.`;
    return "";
  }

  function rulesFor(hz) {
    if (!hz) return [];
    const out = [];
    [...new Set(hz)].forEach(c => { const x = charRule(c); if (x) out.push(["root", x]); });
    return out.slice(0, 2);
  }

  const hookIcon = k => icon(k === "story" ? "book" : k === "bridge" ? "bubbles" : k === "root" ? "parts" : "bulb");

  ICON_PATHS.parts = "M4 4h9v9H4zM11 11h9v9h-9z";
  ICON_PATHS.sun = "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4";
  ICON_PATHS.moon = "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z";
  ICON_PATHS.sunrise = "M3 18h18M6 18a6 6 0 0 1 12 0M12 4v4M4.9 9.9l1.4 1.4M19.1 9.9l-1.4 1.4M9 6l3-3 3 3";
  ICON_PATHS.sunset = "M3 18h18M6 18a6 6 0 0 1 12 0M12 3v5M9 5l3 3 3-3M4.9 9.9l1.4 1.4M19.1 9.9l-1.4 1.4";
  ICON_PATHS.walk = "M13 4a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM10 22l2-7 3 3v4M7 12l3-5h4l3 4M12 15l-1-4";
  ICON_PATHS.bookmark = "M6 3h12v18l-6-4-6 4z";
  ICON_PATHS.check = "M4 12.5l5 5L20 6.5";
  ICON_PATHS.globe = "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c2.5 2.5 3.5 5.5 3.5 9s-1 6.5-3.5 9c-2.5-2.5-3.5-5.5-3.5-9s1-6.5 3.5-9z";
  ICON_PATHS.compass = "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM15.5 8.5l-2 5-5 2 2-5z";
  ICON_PATHS.copy = "M8 8h12v12H8zM4 16V4h12";


  /* the day plan: when each kind of practice helps most */

  const DAY_PLAN = [
    ["sunrise", "Morning, with coffee (5 to 10 minutes)", "Review what's due in Practice.", "Sleep has just consolidated yesterday's words. Pulling them back out now is retrieval practice at the moment it pays off most."],
    ["walk", "Commute, walks, chores (a few minutes)", "Shadow three sentences or do a round of the tone trainer.", "Short sessions spread through the day are spacing in action, and listening while you move uses time you'd lose anyway."],
    ["sun", "Through the day", "Notice one thing and name it in your head in the new language. Try to build a sentence with the translate box.", "Making your own sentences (generation) and relating them to your own life (self-reference) both deepen memory."],
    ["bowl", "Meals with family", "Use one sentence for real. Ask them to correct you, then save it to your phrasebook.", "Real use, real feedback and real emotion make the strongest memories, and it's how children learn: through people they care about."],
    ["sunset", "Evening (10 minutes)", "Learn today's new sentences. Write a hook for any word that won't stick, and check Rules and roots for why the sentence is built that way.", "Understanding the pattern means you remember one rule instead of a hundred words."],
    ["moon", "Before bed (2 minutes)", "Take one last look at today's new sentences, then sleep.", "Words learned before sleep get folded into long-term memory overnight."],
    ["calendar", "Once a week", "Browse a new topic. Save what you'd actually say, and mark what you already know.", "Your phrasebook becomes your own curriculum, and Practice skips sentences you've marked as known."],
  ];

  function nowTip() {
    const h = new Date().getHours();
    if (h >= 5 && h < 11) return ["sunrise", "now_morning"];
    if (h >= 11 && h < 17) return ["sun", "now_day"];
    if (h >= 17 && h < 21) return ["sunset", "now_evening"];
    return ["moon", "now_night"];
  }


  /* rules and roots guide */

  const RULES = [
    {
      ico: "brain", h: "Why rules beat memorizing",
      intro: "Once you see a pattern, a hundred words become one rule plus a few exceptions. That is what it feels like to grok a language. Each language below has a short list of axioms: the rules everything else is built on.",
      items: [
        "Cognates are a free route to new words, but only when the languages are related. A 2026 study of learners of English found that Spanish and German speakers recalled cognates more easily, while Chinese speakers got no such boost. For Chinese, character parts and sound families do the same job.",
      ],
    },
    {
      ico: "parts", h: "Chinese: Taishanese, Cantonese and Mandarin",
      intro: "All three share one grammar and one writing system. Learn the rules once and they carry over.",
      items: [
        "<b>Verbs never change.</b> 我食, 你食, 佢食: I eat, you eat, she eats. There are no conjugation tables at all.",
        "<b>Time comes from words, not endings.</b> 尋日 yesterday, 聽日 tomorrow. Small markers say whether something is done or ongoing: 咗 zo2 / 了 le (done), 緊 gan2 / 在 zài (in progress), 過 gwo3 / guò (have ever done).",
        "<b>Order: who, when, where, then the action.</b> 我 聽日 喺屋企 食飯 is \"I tomorrow at home eat\".",
        "<b>Questions keep the statement's word order.</b> Add a particle (嗎 ma, 呀 aa, 未 mei6 \"yet?\") or say the verb both ways: 去唔去 \"go not go?\", 係唔係 \"is or isn't?\".",
        "<b>Nouns need a counter.</b> Not \"one book\" but \"one 本 book\": 一本書, 一隻狗, 一個人. 個 go3 / gè is the safe default.",
        "<b>Tone is part of the word.</b> 媽 maa1 is mother, 馬 maa5 is horse. Treat tone like a vowel, not like an accent.",
        "<b>Compounds explain themselves.</b> 電 electric + 話 speech = telephone. 電 + 腦 brain = computer. 飛 fly + 機 machine = plane. 火 fire + 車 cart = train. In Cantonese, 雪 snow + 櫃 cabinet = fridge.",
        "<b>About 80% of characters are a meaning part plus a sound part.</b> 媽 = 女 woman + 馬 maa. 嗎 = 口 mouth + 馬 maa: a spoken \"ma\". The meaning part tells you the category: 氵 water, 忄 heart, 口 mouth, 扌 hand, 目 eye, 飠 food, 訁 speech, 辶 movement. 月 on the left usually means body, because it was once 肉 flesh: 肚 belly, 腳 foot, 腦 brain.",
        "<b>Cantonese spoken words are 口 plus a sound.</b> 嘅 = 口 + 既 gei. 咗 = 口 + 左 zo. 嚟 = 口 + 黎 lai. 喺 = 口 + 係 hai. 咩 = 口 + 羊 sheep, because sheep say \"meh\".",
        "<b>Taishanese to Cantonese is a regular sound shift.</b> Cantonese s often becomes Taishanese ɬ (the Welsh \"ll\"): 三 saam1 becomes ɬam33. Cantonese t often becomes h: 頭 tau4 becomes həu22. Learn the shift and you can guess many Taishanese words from the Cantonese.",
        "<b>Cantonese kept old endings that Mandarin lost.</b> 十 sap6 / shí, 六 luk6 / liù, 三 saam1 / sān. The -p, -t, -k and -m endings are older, and they also show up in Korean and Japanese readings of the same characters.",
        "<b>Chinese numbers are perfectly regular.</b> 十一 is ten-one (11) and 二十 is two-ten (20). Compare French quatre-vingt-douze, four-twenty-twelve (92), or German einundzwanzig, one-and-twenty (21).",
      ],
    },
    {
      ico: "book", h: "Spanish and French: Latin's children",
      intro: "Close to 60% of English vocabulary came in through Latin and French (counts vary), so you already know thousands of Spanish and French words in disguise.",
      items: [
        "<b>Swap the ending.</b> -tion becomes -ción / -tion (nation, nación). -ty becomes -dad / -té (city, ciudad, cité). -ly becomes -mente / -ment (rapidly, rápidamente, rapidement). -ous becomes -oso / -eux (famous, famoso, fameux).",
        "<b>Spanish puts e- before s plus a consonant.</b> school, escuela. student, estudiante. special, especial. French did the same, then dropped the s: école, étudiant.",
        "<b>A French circumflex often marks a lost s.</b> forêt forest, hôpital hospital, fête feast, île isle. Put the s back and the English appears.",
        "<b>The verb ending carries the person.</b> In Spanish, como is I eat and comes is you eat, so the pronoun can drop. One set of endings (-o, -as, -a, -amos, -an) works for thousands of verbs.",
        "<b>Every noun has a gender.</b> Learn the article with the noun: la leche, le lait.",
        "<b>Grimm's law links them back to English.</b> Latin p corresponds to English f: padre, father. pie, foot. pez, fish. Latin hard c corresponds to h: corazón, heart. cien, hundred. Latin d corresponds to t: dos, two. diente, tooth.",
      ],
    },
    {
      ico: "house", h: "German: English's sibling",
      intro: "German and English split only about 1,500 years ago. Most German sounds map to English by a handful of regular rules.",
      items: [
        "<b>English t is German z, ss or s:</b> ten zehn, tongue Zunge, water Wasser, eat essen, what was, that das.",
        "<b>English p is German pf or f:</b> apple Apfel, pepper Pfeffer, ship Schiff, help helfen.",
        "<b>English d is German t:</b> day Tag, drink trinken, door Tür, daughter Tochter.",
        "<b>English th is German d:</b> three drei, thank danken, thing Ding, the der.",
        "<b>English k and gh are German ch:</b> make machen, book Buch, night Nacht, light Licht, eight acht.",
        "<b>English v is German b:</b> have haben, give geben, over über.",
        "<b>The verb comes second.</b> Heute gehe ich: \"today go I\". In yes/no questions and commands it goes first. After weil (because) and dass (that) it goes to the end.",
        "<b>Nouns stack like Chinese compounds.</b> Kühlschrank (cool-cabinet) is a fridge, like Cantonese 雪櫃 (snow-cabinet). Flugzeug (fly-thing) is a plane, like 飛機 (fly-machine). Krankenhaus (sick-house) is a hospital.",
        "<b>Nouns are capitalized and have three genders:</b> der, die, das. Learn the article with the word.",
      ],
    },
    {
      ico: "compass", h: "Every language has its own axioms",
      intro: "The linguist Roman Jakobson put it this way: languages differ in what they must say, not in what they can say. Each one makes you notice different things.",
      items: [
        "<b>No left or right.</b> In Guugu Yimithirr, an Aboriginal Australian language, you don't have a left hand. You have a north or south hand, depending on which way you're facing. Speakers keep track of compass directions all day long, without thinking.",
        "<b>Chinese makes you name the relative exactly.</b> 嫲嫲 is your father's mother and 婆婆 is your mother's mother. 哥哥 is your older brother and 弟弟 your younger. English \"grandma\" and \"brother\" don't say which. In Chinese you have to.",
        "<b>Spanish, French and German make you pick a tense and a gender in every sentence.</b> Chinese doesn't, but it makes you pick a counter and a tone.",
        "<b>Time has a direction.</b> Chinese says 上個月 (up month) for last month and 下個月 (down month) for next month. 前日 (the front day) is the day before yesterday, so the past is in front of you, the opposite of English \"looking forward\".",
        "<b>Being polite is built into some grammars.</b> Spanish usted, French vous and German Sie are a formal \"you\". Mandarin has 您. Cantonese mostly uses titles instead: 阿姨, 姨丈.",
      ],
    },
  ];

  const READING = [
    ["Learning a second language", [
      ["Lightbown & Spada, How Languages Are Learned (Oxford)", "https://openlibrary.org/search?q=How+Languages+Are+Learned+Lightbown"],
      ["Paul Nation, Learning Vocabulary in Another Language (Cambridge)", "https://cambridge.org/core/books/learning-vocabulary-in-another-language/491314AA1B451AD04F3536000F1C9F0D"],
      ["Stephen Krashen, Principles and Practice in Second Language Acquisition (1982): comprehensible input, influential but debated", "https://openlibrary.org/search?q=Principles+and+Practice+in+Second+Language+Acquisition"],
      ["Rod Ellis, The Study of Second Language Acquisition (Oxford)", "https://openlibrary.org/search?q=The+Study+of+Second+Language+Acquisition+Ellis"],
      ["Michael Lewis, The Lexical Approach (1993): learning language in chunks", "https://openlibrary.org/search?q=The+Lexical+Approach+Michael+Lewis"],
    ]],
    ["How memory and learning work", [
      ["Brown, Roediger & McDaniel, Make It Stick (2014)", "https://openlibrary.org/search?q=Make+It+Stick+Brown+Roediger"],
      ["Stanislas Dehaene, How We Learn (2020)", "https://openlibrary.org/search?q=How+We+Learn+Dehaene"],
      ["Lev Vygotsky, Mind in Society (1978): learning with someone just ahead of you", "https://openlibrary.org/search?q=Mind+in+Society+Vygotsky"],
      ["Jerome Bruner, Child's Talk: Learning to Use Language (1983): scaffolding", "https://openlibrary.org/search?q=Child%27s+Talk+Bruner"],
    ]],
    ["Language, mind and culture", [
      ["Guy Deutscher, Through the Language Glass (2010)", "https://www.bookshare.org/browse/book/390041"],
      ["Guy Deutscher, The Unfolding of Language (2005): where grammar comes from", "https://openlibrary.org/search?q=The+Unfolding+of+Language+Deutscher"],
      ["Stephen Levinson, Space in Language and Cognition (Cambridge, 2003)", "https://openlibrary.org/search?q=Space+in+Language+and+Cognition+Levinson"],
      ["Edward Sapir, Language (1921)", "https://openlibrary.org/search?q=Sapir+Language+1921"],
      ["Steven Pinker, The Language Instinct (1994): the case for what all languages share", "https://openlibrary.org/search?q=The+Language+Instinct+Pinker"],
      ["Lera Boroditsky, How language shapes thought (Scientific American, 2011)", "https://www.cs.bu.edu/courses/cs111/old/18spring/files/ps0/language_shapes.pdf"],
      ["Levinson (1997), Spatial description in Guugu Yimithirr", "https://pure.mpg.de/pubman/item/item_66622_3/component/file_66623/1997_Spatial_description_in_Guugu_Yimithirr.pdf"],
    ]],
    ["Chinese in particular", [
      ["Matthews & Yip, Cantonese: A Comprehensive Grammar (Routledge)", "https://openlibrary.org/search?q=Cantonese+A+Comprehensive+Grammar"],
      ["Phonetic components: the key to 80% of Chinese characters (Hacking Chinese)", "https://www.hackingchinese.com/phonetic-components-part-1-the-key-to-80-of-all-chinese-characters/"],
    ]],
    ["Research papers on arXiv", [
      ["Tabibian et al., Optimizing Human Learning (2017): review when recall is about to slip", "https://arxiv.org/abs/1712.01856"],
      ["Reddy et al., Unbounded Human Learning (2016): adding new items too fast swamps learning", "https://arxiv.org/abs/1602.07032"],
      ["Beinborn et al., What Makes a Word Hard to Learn? (2026): cognates help Spanish and German speakers, not Chinese", "https://arxiv.org/abs/2605.12281"],
      ["Wang, Perceptual training of Mandarin tones for English speakers (2023)", "https://arxiv.org/abs/2309.13513"],
      ["Georgiou, Nonnative speech perception and production with an app (2025)", "https://arxiv.org/abs/2503.22705"],
      ["Anderson, Vocabulary and the Brain: evidence from neuroimaging", "https://arxiv.org/abs/1611.10003"],
    ]],
  ];


  /* every Chinese character in explanations gets its sound on top, so nothing is ever shown without a pronunciation */

  let ZR = null;

  function zhSounds() {
    if (ZR) return ZR;
    const cnt = new Map();
    PHRASES.forEach(p => (p.yue || []).forEach(t => {
      const cs = [...(t.hz || "")];
      const ss = String(t.rom || "").trim().split(/\s+/);
      if (cs.length !== ss.length) return;
      cs.forEach((c, i) => { const k = c + "|" + ss[i]; cnt.set(k, (cnt.get(k) || 0) + 1); });
    }));
    ZR = new Map();
    const best = new Map();
    cnt.forEach((n, k) => { const [c, s] = k.split("|"); if (!best.has(c) || n > best.get(c)) { best.set(c, n); ZR.set(c, s); } });
    Object.entries(PHON).forEach(([c, v]) => { if (!ZR.has(c)) ZR.set(c, v[0]); });
    JYUT_RAW.split(",").forEach(x => { const c = x[0]; if (c && !ZR.has(c)) ZR.set(c, x.slice(1)); });
    return ZR;
  }

  function zhRuby(html) {
    const m = zhSounds();
    return String(html).split(/(<[^>]+>)/).map(part => part.startsWith("<") ? part : part.replace(/[㐀-鿿]/g, c => m.has(c) ? `<ruby>${c}<rt>${esc(romText("yue", m.get(c)))}</rt></ruby>` : c)).join("");
  }
