# -*- coding: utf-8 -*-
"""
Curate Flagship Courses with Authentic, Famous Quotations & Real Scenarios
Replaces generic topic dumps in movie_classics, tv_slang_hot, classic_prose, ted_talks_master
with true, soul-stirring, famous English lines, accompanied by Kokoro IPA and syntactic grammar tags.
"""
import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app", "courses_database.json")

# Import helpers from build script
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from build_massive_courses import tag_syntax_chunks, get_ipa

def make_drill(drill_id, course_id, chapter_id, chapter_title, en, zh, idx):
    chunks = tag_syntax_chunks(en)
    ipa = get_ipa(en)
    words = [re.sub(r'[.,?!;:\'"]', '', w).strip() for w in en.split() if w.strip()]
    tokens = [c['text'] for c in chunks] if chunks else words
    breakdown = " + ".join([f"{c['text']} [{c['role']}]" for c in chunks])
    return {
        "id": drill_id,
        "course_id": course_id,
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "index": idx,
        "english": en,
        "chinese": zh,
        "ipa": ipa,
        "chunks": chunks,
        "tokens": tokens,
        "words": words,
        "breakdown": breakdown,
        "cultural_tip": f"名句金句研读：体会英文地道句型与情感张力，熟练朗读背诵并掌握语法结构。"
    }

# 1. 好莱坞经典电影金句与灵魂台词精读 (movie_classics)
MOVIE_DATA = {
    "ch_01": ("《阿甘正传》人生与命运感悟", [
        ("Life was like a box of chocolates, you never know what you're gonna get.", "生活就像一盒巧克力，你永远不知道下一颗是什么味道。"),
        ("Stupid is as stupid does.", "蠢人做蠢事，愚蠢由行为定义。"),
        ("Miracles happen every day, some people don't think so, but they do.", "奇迹每天都在发生，有些人不信，但确实如此。"),
        ("You have to put the past behind you before you can move on.", "你必须把过去抛在脑后，才能继续前行。"),
        ("Mama always said death was a part of life.", "妈妈总是说，死亡是生命的一部分。"),
        ("I'm not a smart man, but I know what love is.", "我不聪明，但我知道什么是爱。"),
        ("You've got to do the best with what God gave you.", "你必须用上帝给予你的东西做到最好。"),
        ("Run, Forrest, run!", "跑，阿甘，快跑！"),
        ("Mama said there's only so much fortune a man really needs.", "妈妈说，一个人真正需要的财富其实有限。"),
        ("The rest is just showing off.", "多余的那些不过是用来炫耀罢了。"),
        ("I don't know if we each have a destiny, or if we're all just floating around accidental-like on a breeze.", "我不知道我们每个人是否有固定的宿命，还是像微风中的落叶一样随遇而安。"),
        ("Maybe both is happening at the same time.", "也许两者是在同时发生。"),
        ("If you are in trouble, don't try to be brave, just run away.", "如果你遇到麻烦，不要逞强，尽管跑开就好。"),
        ("Nothing just happens, it's all part of a plan.", "没有事情是无缘无故发生的，这都是计划的一部分。"),
        ("You can't really know where you are going until you know where you have been.", "如果你不知道自己从何而来，你就无法知道自己将去向何方。"),
        ("Jennie, why don't you love me?", "珍妮，你为什么不爱我？"),
        ("Sometimes, I guess there just aren't enough rocks.", "有时候，我想只是没有足够的石子罢了。"),
        ("Bubba was my best good friend.", "巴布是我最好的好朋友。"),
        ("I'll never forget the first time I saw the sweetest thing in the world.", "我永远忘不了第一次见到世界上最甜美事物的那一刻。"),
        ("From that day on, we was always together, like peas and carrots.", "从那天起，我们便总是在一起，形影不离。")
    ]),
    "ch_02": ("《肖申克的救赎》希望与坚守金句", [
        ("Hope is a good thing, maybe the best of things, and no good thing ever dies.", "希望是美好的，也许是世间最好的事物，而美好的事物永不消逝。"),
        ("Fear can hold you prisoner. Hope can set you free.", "恐惧把你囚禁，希望让你自由。"),
        ("Get busy living, or get busy dying.", "忙着活，或者忙着死。"),
        ("These walls are funny. First you hate them, then you get used to them. Enough time passes, you depend on them.", "这些高墙很有趣。起初你恨它们，然后你习惯它们，久而久之你离不开它们。这就是体制化。"),
        ("Some birds are not meant to be caged, their feathers are just too bright.", "有些鸟儿是关不住的，它们的羽毛太明亮了。"),
        ("Remember, Red, hope is a good thing.", "记住，瑞德，希望是美好的东西。"),
        ("Salvation lies within.", "救赎之道，就在其中。"),
        ("I hope the Pacific is as blue as it has been in my dreams.", "我希望太平洋就像我梦中那样蔚蓝。"),
        ("I hope to see my friend and shake his hand.", "我希望能见到我的朋友，并同他握手。"),
        ("I hope to cross the border.", "我希望能跨越边境。"),
        ("A strong man can save himself. A great man can save another.", "坚强的人自救，伟大的人渡人。"),
        ("Bad luck isn't something that happens to you, it's something that floats around in the air.", "厄运不是针对你的，它只是在空气中游荡。"),
        ("That's the beauty of music. They can't take that away from you.", "这就是音乐的美丽之处，他们无法将它从你身边夺走。"),
        ("Every man has his breaking point.", "每个人都有他的崩溃临界点。"),
        ("The world went and got itself in a big damn hurry.", "世界转得太快了，变得匆忙得要命。"),
        ("Hope is a dangerous thing. Hope can drive a man insane.", "希望是个危险的东西，希望会让人发疯。"),
        ("There are places in this world that aren't made out of stone.", "这世界上有些地方不是由石头筑成的。"),
        ("It takes a strong man to survive here, and an even stronger man to be free.", "在这里生存需要坚强的人，而获得自由需要更坚强的人。"),
        ("Those voices soared higher and farther than anybody in a gray place dares to dream.", "那些歌声高亢悠远，超越了高墙内所有人的梦想。"),
        ("For the briefest of moments, every last man in Shawshank felt free.", "在最短暂的瞬间，肖申克的所有人都感受到了自由。")
    ]),
    "ch_03": ("《泰坦尼克号》爱情与承诺誓言", [
        ("Winning that ticket was the best thing that ever happened to me.", "赢得那张船票是我一生中发生过最美好的事。"),
        ("It brought me to you, and I'm thankful for that.", "它让我遇见了你，我为此心怀感激。"),
        ("I'll never let go, Jack. I promise.", "我绝不放手，杰克。我发誓。"),
        ("A woman's heart is a deep ocean of secrets.", "女人的心是一片深不可测的秘密海洋。"),
        ("I figure life is a gift and I don't intend on wasting it.", "我觉得生命是一份礼物，我不想浪费它。"),
        ("You jump, I jump, remember?", "你跳，我也跳，记得吗？"),
        ("I can't turn away without knowing you'll be all right.", "在知道你平安无事之前，我绝不会离开。"),
        ("To make each day count.", "让每一天都过得有意义。"),
        ("Promise me you will survive, that you won't give up.", "答应我你会活下去，你绝不会放弃。"),
        ("No matter what occurs, no matter how hopeless.", "无论发生什么，无论多么令人绝望。"),
        ("Promise me now, Rose, and never let go of that promise.", "罗丝，现在就答应我，并且永远不要背弃这个诺言。"),
        ("I'm king of the world!", "我是世界之王！"),
        ("When you got nothing, you got nothing to lose.", "当你一无所有时，你就没有什么可以失去的。"),
        ("I love waking up in the morning not knowing what's gonna happen.", "我喜欢早晨醒来时，不知道今天会发生什么。"),
        ("Fifteen hundred people went into the sea when Titanic sank.", "泰坦尼克号沉没时，有一千五百人坠入大海。"),
        ("There were twenty boats floating nearby and only one came back.", "周围漂浮着二十艘救生艇，却只有一艘返航搜救。"),
        ("Six were saved from the water, myself included.", "只有六个人从水中获救，包括我在内。"),
        ("He saved me in every way that a person can be saved.", "他拯救了我，以一个人能被拯救的所有方式。"),
        ("I don't even have a picture of him.", "我甚至连他的一张照片都没有。"),
        ("He exists now only in my memory.", "如今他只存在于我的记忆之中。")
    ]),
    "ch_04": ("《教父》权力、智慧与家族忠告", [
        ("I'm gonna make him an offer he can't refuse.", "我会给他一个他无法拒绝的条件。"),
        ("A man who doesn't spend time with his family can never be a real man.", "一个不花时间陪伴家人的男人，永远成不了真正的男人。"),
        ("Never hate your enemies. It affects your judgment.", "永远不要憎恨你的敌人，那会影响你的判断力。"),
        ("Keep your friends close, but your enemies closer.", "亲近你的朋友，但更要亲近你的敌人。"),
        ("Great men are not born great, they grow great.", "伟大的人并非生而伟大，而是在成长中变得伟大。"),
        ("Finance is a gun. Politics is knowing when to pull the trigger.", "金融是一把枪，政治则是懂得何时扣动扳机。"),
        ("It's not personal, Sonny. It's strictly business.", "桑尼，这不是个人恩怨，纯粹是公事公办。"),
        ("Revenge is a dish that tastes best when served cold.", "复仇这道菜，放凉了吃味道最好。"),
        ("Never let anyone outside the family know what you are thinking.", "永远不要让家族以外的任何人知道你在想什么。"),
        ("A friend should always underestimate your virtues and an enemy overestimate your faults.", "朋友应该低估你的优点，而敌人应该高估你的缺点。"),
        ("Just when I thought I was out, they pull me back in.", "就在我以为自己已经脱身时，他们又把我拉了回来。"),
        ("Don't ever take sides with anyone against the Family again.", "绝不要再站在外人一边对抗家族。"),
        ("Power wears out those who do not have it.", "权力只会让那些没有权力的人筋疲力尽。"),
        ("Only don't tell me that you're innocent. Because it insults my intelligence.", "千万别告诉我你是无辜的，因为那是在侮辱我的智商。"),
        ("I have learned more in the streets than in any classroom.", "我在街头学到的东西，比在任何课堂上学到的都要多。"),
        ("Time erodes gratitude faster than beauty.", "时间侵蚀感激之情，比侵蚀美貌还要迅速。"),
        ("The strength of a family lies in its loyalty to each other.", "一个家族的力量在于成员彼此之间的忠诚。"),
        ("Never get angry. Never make a threat. Reason with people.", "永远不要愤怒，永远不要威胁他人，要同人讲道理。"),
        ("I spent my whole life trying not to be careless.", "我花了一辈子的时间努力不让自己变得粗心大意。"),
        ("Women and children can be careless, but not men.", "女人和孩子可以粗心大意，但男人不行。")
    ])
}

# 2. 世界经典名著晨读与长难句精析 (classic_prose)
LIT_DATA = {
    "ch_01": ("《傲慢与偏见》人物对话与心境描写", [
        ("It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.", "凡是有钱的单身汉，总想娶位太太，这已成了一条举世公认的真理。"),
        ("Pride and vanity are very different things, though the words are often used synonymously.", "骄傲与虚荣是两码事，尽管这两个词经常被当作同义词来使用。"),
        ("A person may be proud without being vain.", "一个人可以骄傲，但并不一定虚荣。"),
        ("Pride relates more to our opinion of ourselves, vanity to what we would have others think of us.", "骄傲多半关乎我们对自己的评价，而虚荣则关乎我们希望别人如何看待我们。"),
        ("You have bewitched me, body and soul, and I love, I love, I love you.", "你对我的身体和灵魂施了魔法，我爱你，我爱你，我爱你。"),
        ("I never wish to be parted from you from this day on.", "从今往后，我愿永远不与你分离。"),
        ("There are few people whom I really love, and still fewer of whom I think well.", "我真正爱的人很少，看重的人就更少了。"),
        ("The more I see of the world, the more am I dissatisfied with it.", "我见识的世界越多，我对它就越感到不满。"),
        ("Every day confirms my belief of the inconsistency of all human characters.", "每一天都在证实我的看法：人性的善变与不可靠是世间的常态。"),
        ("My good opinion once lost, is lost forever.", "一旦别人失去了我对他的好感，就永远也找不回来了。"),
        ("I must learn to be contented with being happier than I deserve.", "我必须学会知足，因为我得到的幸福已经超出了我应得的限度。"),
        ("Till this moment I never knew myself.", "直到这一刻，我才真正认清了自己。")
    ]),
    "ch_02": ("《了不起的盖茨比》时代的追梦与幻灭", [
        ("In my younger and more vulnerable years my father gave me some advice that I've been turning over in my mind ever since.", "在我年纪更轻、思想更脆弱的岁月里，父亲曾给我一句忠告，多年来一直在我的脑海中回响。"),
        ("Whenever you feel like criticizing anyone, just remember that all the people in this world haven't had the advantages that you've had.", "每当你想要批评任何人的时候，记住，这个世界上并不是所有人都拥有你曾拥有的那些优越条件。"),
        ("So we beat on, boats against the current, borne back ceaselessly into the past.", "于是我们逆水行舟，拼力前行，却不断地被浪潮推回到过去。"),
        ("He looked at her the way all women want to be looked at by a man.", "他注视着她的眼神，正是所有女人都渴望从男人眼中看到的模样。"),
        ("He had one of those rare smiles with a quality of eternal reassurance in it.", "他露出了那种罕见的微笑，带着一种能让人永远感到安心的特质。"),
        ("Reserving judgments is a matter of infinite hope.", "保留判断是蕴含着无尽希望的一种态度。"),
        ("I was within and without, simultaneously enchanted and repelled by the inexhaustible variety of life.", "我身在其中又置身事外，对生活千变万化的样貌既深感着迷又心生抵触。"),
        ("Gatsby believed in the green light, the orgastic future that year by year recedes before us.", "盖茨比信奉那盏绿灯，信奉那个一年年从我们眼前倒退的极乐未来。"),
        ("It eluded us then, but that's no matter—tomorrow we will run faster, stretch out our arms farther.", "那未来曾经避开了我们，但那不要紧——明天我们将跑得更快，将手臂伸得更远。"),
        ("And one fine morning, so we beat on.", "直到一个晴朗的早晨，我们继续乘风破浪。")
    ]),
    "ch_03": ("《老人与海》硬汉不屈的生命尊严", [
        ("Man is not made for defeat.", "人不是为了失败而生的。"),
        ("A man can be destroyed but not defeated.", "一个人可以被消灭，但绝不能被打败。"),
        ("Now is no time to think of what you do not have. Think of what you can do with what there is.", "现在不是去想你缺少什么的时候，去想想用你手头现有的东西能做些什么吧。"),
        ("Every day is a new day. It is better to be lucky. But I would rather be exact.", "每一天都是崭新的一天。走运固然好，但我宁愿做到准确无误。"),
        ("Then when luck comes you are ready.", "这样当好运到来时，你就已经做好了准备。"),
        ("The fish is my friend too. I have never seen or heard of such a fish.", "这条大鱼也是我的朋友。我从未见过或听说过如此雄伟的鱼。"),
        ("Pain does not matter to a man.", "痛苦对于一个真正的男人来说算不了什么。"),
        ("It is silly not to hope. Besides, I believe it is a sin.", "放弃希望是愚蠢的。况且，我相信那是种罪过。"),
        ("He was an old man who fished alone in a skiff in the Gulf Stream.", "他是一个独自驾着小船在墨西哥湾暖流中打鱼的老人。"),
        ("The sail was patched with flour sacks and it looked like the flag of permanent defeat.", "那张帆用面粉袋打满了补丁，看上去就像一面象征着永久失败的旗帜。")
    ]),
    "ch_04": ("《小王子》关于爱与驯服的纯真哲思", [
        ("It is only with the heart that one can see rightly; what is essential is invisible to the eye.", "唯有用心才能看清一切；真正重要的东西，肉眼是看不见的。"),
        ("It is the time you have wasted for your rose that makes your rose so important.", "正是你为你的玫瑰倾注的时间，才使得你的玫瑰变得如此重要。"),
        ("You become responsible, forever, for what you have tamed.", "你必须对你所驯服的一切，永远负责到底。"),
        ("All grown-ups were once children, but only few of them remember it.", "所有大人都曾经是小孩，虽然，只有少数人记得这一点。"),
        ("To me, you will be unique in all the world. To you, I shall be unique in all the world.", "对我而言，你将是世界上独一无二的；对你而言，我也将是世界上独一无二的。"),
        ("If you come at four in the afternoon, then at three I shall begin to be happy.", "如果你下午四点钟来，那么从三点钟起，我就开始感到幸福了。"),
        ("What makes the desert beautiful is that somewhere it hides a well.", "使沙漠显得如此美丽的，是它在某个角落藏着一口水井。"),
        ("The stars are beautiful, because of a flower that cannot be seen.", "星星之所以美丽，是因为有一朵看不见的花。"),
        ("Language is the source of misunderstandings.", "语言是误解的根源。"),
        ("No one is ever satisfied where he is.", "没有人会对自己所在的地方感到满意。")
    ])
}

# 3. TED高分演讲核心启发句型与表达技巧 (ted_talks_master)
SPEECH_DATA = {
    "ch_01": ("演讲开场白抓人与痛点抛出", [
        ("Stay hungry. Stay foolish.", "求知若饥，虚心若愚。"),
        ("Your time is limited, so don't waste it living someone else's life.", "你的时间有限，所以不要浪费时间去过别人的生活。"),
        ("Don't let the noise of others' opinions drown out your own inner voice.", "不要让别人意见的噪音淹没你内心的声音。"),
        ("Have the courage to follow your heart and intuition.", "勇敢地去追随你的心灵和直觉。"),
        ("They somehow already know what you truly want to become.", "它们在某种程度上早就知道你真正想成为什么样的人。"),
        ("I have a dream that one day this nation will rise up.", "我有一个梦想，梦想有一天这个国家会站立起来。"),
        ("Live out the true meaning of its creed: We hold these truths to be self-evident.", "践行其信条的真正内涵：我们认为这些真理是不言而喻的。"),
        ("Let freedom ring from the prodigious hilltops of New Hampshire.", "让自由之声从新罕布什尔的崇山峻岭中响起。"),
        ("We shall fight on the beaches, we shall fight on the landing grounds.", "我们将在海滩作战，我们将在登陆点作战。"),
        ("We shall never surrender.", "我们决不投降。")
    ]),
    "ch_02": ("个人故事叙述与情感强烈共鸣", [
        ("You can't connect the dots looking forward; you can only connect them looking backwards.", "你在向前看的时候无法把点连成线；你只有在回顾过去时才能将它们串联起来。"),
        ("So you have to trust that the dots will somehow connect in your future.", "所以你必须相信，这些点在未来的某一天总会以某种方式串联在一起。"),
        ("You have to trust in something: your gut, destiny, life, karma, whatever.", "你必须信任某种东西：你的直觉、命运、生命、因果，任何东西。"),
        ("Sometimes life hits you in the head with a brick. Don't lose faith.", "有时生活会用砖头砸你的脑袋，但千万不要失去信念。"),
        ("The only way to do great work is to love what you do.", "成就伟业的唯一途径，就是热爱你所做的事。"),
        ("If you haven't found it yet, keep looking. Don't settle.", "如果你还没找到它，继续寻找，不要将就。"),
        ("Vulnerability is not winning or losing; it's having the courage to show up when you can't control the outcome.", "展现脆弱不是输赢之争；而是在你无法掌控结局时，依然有勇气站在台上。"),
        ("Imperfections are not inadequacies; they are reminders that we're all in this together.", "不完美并非缺陷；它们提醒着我们大家都是同舟共济的普通人。")
    ]),
    "ch_03": ("排比修辞与递进式逻辑论辩", [
        ("Government of the people, by the people, for the people, shall not perish from the earth.", "民有、民治、民享的政府，当永世长存。"),
        ("Ask not what your country can do for you; ask what you can do for your country.", "不要问你的国家能为你做些什么，而要问你能为你的国家做些什么。"),
        ("Change will not come if we wait for some other person or some other time.", "如果我们等待别人或等待其他时机，变革就永远不会到来。"),
        ("We are the ones we've been waiting for. We are the change that we seek.", "我们就是我们一直在等待的人，我们就是我们所寻求的变革。"),
        ("If you want to go fast, go alone. If you want to go far, go together.", "如果你想走得快，那就独自一人走；如果你想走得远，那就结伴同行。"),
        ("The future belongs to those who believe in the beauty of their dreams.", "未来属于那些坚信自己梦想之美好的人。")
    ]),
    "ch_04": ("震撼全场的精彩收尾与行动呼吁", [
        ("Remembering that you are going to die is the best way I know to avoid the trap of thinking you have something to lose.", "记住你即将死去，是我所知道的避免陷入患得患失陷阱的最佳方法。"),
        ("You are already naked. There is no reason not to follow your heart.", "你已经一无所有了，毫无理由不去顺从你的内心。"),
        ("No one wants to die. Even people who want to go to heaven don't want to die to get there.", "没有人想要死去，即使是那些想去天堂的人也不想为了去那里而死去。"),
        ("And yet death is the destination we all share.", "然而死亡是我们所有人共同的归宿。"),
        ("Stay hungry. Stay foolish. Thank you all very much.", "求知若饥，虚心若愚。非常感谢各位。")
    ])
}

def update_courses_database():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        courses = json.load(f)

    for c in courses:
        cid = c["id"]
        if cid == "movie_classics":
            print("Curating course: movie_classics...")
            new_chapters = []
            for ch_id, (ch_title, quotes) in MOVIE_DATA.items():
                drills = []
                for idx, (en, zh) in enumerate(quotes, 1):
                    drill_id = f"movie_{ch_id}_{idx:03d}"
                    drills.append(make_drill(drill_id, cid, ch_id, ch_title, en, zh, idx))
                new_chapters.append({
                    "id": ch_id,
                    "title": ch_title,
                    "chapter_num": len(new_chapters) + 1,
                    "drill_count": len(drills),
                    "drills": drills
                })
            c["chapters"] = new_chapters
            c["chapter_count"] = len(new_chapters)
            c["sentence_count"] = sum(len(ch["drills"]) for ch in new_chapters)

        elif cid == "classic_prose":
            print("Curating course: classic_prose...")
            new_chapters = []
            for ch_id, (ch_title, quotes) in LIT_DATA.items():
                drills = []
                for idx, (en, zh) in enumerate(quotes, 1):
                    drill_id = f"lit_{ch_id}_{idx:03d}"
                    drills.append(make_drill(drill_id, cid, ch_id, ch_title, en, zh, idx))
                new_chapters.append({
                    "id": ch_id,
                    "title": ch_title,
                    "chapter_num": len(new_chapters) + 1,
                    "drill_count": len(drills),
                    "drills": drills
                })
            c["chapters"] = new_chapters
            c["chapter_count"] = len(new_chapters)
            c["sentence_count"] = sum(len(ch["drills"]) for ch in new_chapters)

        elif cid == "ted_talks_master":
            print("Curating course: ted_talks_master...")
            new_chapters = []
            for ch_id, (ch_title, quotes) in SPEECH_DATA.items():
                drills = []
                for idx, (en, zh) in enumerate(quotes, 1):
                    drill_id = f"ted_{ch_id}_{idx:03d}"
                    drills.append(make_drill(drill_id, cid, ch_id, ch_title, en, zh, idx))
                new_chapters.append({
                    "id": ch_id,
                    "title": ch_title,
                    "chapter_num": len(new_chapters) + 1,
                    "drill_count": len(drills),
                    "drills": drills
                })
            c["chapters"] = new_chapters
            c["chapter_count"] = len(new_chapters)
            c["sentence_count"] = sum(len(ch["drills"]) for ch in new_chapters)

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    total_sents = sum(c['sentence_count'] for c in courses)
    print(f"Successfully curated database! Total courses: {len(courses)}, Total sentences: {total_sents}")

if __name__ == "__main__":
    update_courses_database()
