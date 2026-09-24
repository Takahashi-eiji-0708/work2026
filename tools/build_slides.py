"""講義スライド（ELI テンプレート・A4横）を生成する。

    python tools/build_slides.py            # 作成済みのバッチまでをすべて生成
スライドは 10 枚程度ずつのバッチ関数に分けて定義している。
"""
from pathlib import Path

from slide_lib import (BLUE, BOTTOM, GRAY, LIGHT, NAVY, ORANGE, ORANGE_PALE, PALE, TEXT, WHITE, W, X0, Y0,
                       Slide, build, para, ps)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "slides" / "template" / "ELI_template.pptx"
OUT = ROOT / "slides" / "ソリューション営業のための生成AIセキュア活用実践.pptx"

GRAY_FILL = "EFEFEF"
CODE_FILL = "F4F4F4"


def batch1():
    slides = []

    # 1 表紙 -----------------------------------------------------------------
    slides.append(Slide("cover", ("ソリューション営業のための\n生成AIセキュア活用実践",
                                  "Copilot × Office で提案活動を体験する2日間")))

    # 2 目次 -----------------------------------------------------------------
    s = Slide("content", "目次")
    chapters = ["生成AIの進化と現状", "Copilot の基本操作とプロンプト設計", "セキュアに使うための留意点",
                "Word × Copilot：商談準備と議事録", "商談後フォロー：メール・社内報告・行動管理",
                "Excel × Copilot：分析と見積", "Word × Copilot：提案書の作成", "PowerPoint × Copilot：提案スライド",
                "自社アプリ ELI Sales Assist の紹介", "営業業務への応用"]
    line = 381000  # 30pt
    top = 1150000
    s.body_placeholder(X0, top, 5900000, line * 10 + 200000,
                       "".join(para(c, size=1600, bullet="num", line_pts=3000) for c in chapters))
    s.box(6350000, top + 40000, 200000, line * 8 - 80000, prst="rightBrace", line=BLUE, line_w=19050)
    s.box(6680000, top + line * 3, 2890000, line * 2,
          ps([("パートA　約3/4", {"bold": True, "size": 1500, "color": WHITE}),
              ("基礎・セキュリティ・Office連携", {"size": 1100, "color": WHITE})]),
          fill=NAVY, prst="roundRect", anchor="ctr")
    s.box(6350000, top + line * 8 + 40000, 200000, line * 2 - 80000, prst="rightBrace", line=ORANGE, line_w=19050)
    s.box(6680000, top + line * 8, 2890000, line * 2,
          ps([("パートB　約1/4", {"bold": True, "size": 1500, "color": WHITE}),
              ("自社アプリ紹介と業務への応用", {"size": 1100, "color": WHITE})]),
          fill=ORANGE, prst="roundRect", anchor="ctr")
    s.text(X0, 5500000, W, 400000,
           para("Day 1：第1章〜第5章　／　Day 2：第6章〜第10章", size=1300, color=GRAY))
    slides.append(s)

    # 3 オリエンテーション ------------------------------------------------------
    s = Slide("content", "オリエンテーション：研修のゴールと進め方")
    s.text(X0, 1030000, W, 340000, para("この研修のゴール", size=1600, bold=True, color=NAVY))
    goals = [("安全に", "入力してよい情報を判断し、マスキングとファクトチェックを習慣にする"),
             ("成果物まで", "議事録・見積・提案書・スライドを、Copilot と一緒に最後まで仕上げる"),
             ("自分の業務で", "自社アプリの例をヒントに、自分の営業業務への応用プランを作る")]
    gap = 230000
    cw = (W - gap * 2) / 3
    for i, (head, body) in enumerate(goals):
        x = X0 + i * (cw + gap)
        s.box(x, 1420000, cw, 1900000, fill=PALE, prst="roundRect", adj={"adj": 8000})
        s.circle_num(x + 200000, 1580000, 520000, i + 1)
        s.text(x + 820000, 1580000, cw - 950000, 520000, para(head, size=2000, bold=True, color=NAVY), anchor="ctr")
        s.text(x + 200000, 2250000, cw - 400000, 950000, para(body, size=1300, line=120000))
    s.text(X0, 3560000, W, 340000, para("進め方", size=1600, bold=True, color=NAVY))
    flow = [("短い講義", "仕組みとルールを押さえる"), ("演習で体感", "みらい商事への提案を進める"),
            ("振り返り・共有", "3名の結果の違いから学ぶ")]
    fw = (W + 150000 * 2) / 3
    for i, (head, body) in enumerate(flow):
        x = X0 + i * (fw - 150000)
        s.box(x, 3950000, fw, 820000,
              ps([(head, {"size": 1500, "bold": True, "color": WHITE, "align": "ctr"}),
                  (body, {"size": 1100, "color": WHITE, "align": "ctr"})]),
              fill=[NAVY, BLUE, "3A96D8"][i], prst="chevron" if i else "homePlate", anchor="ctr",
              adj={"adj": 30000}, inset=(300000, 45720, 300000, 45720))
    notes = [("演習は全体の約6割", PALE, TEXT), ("受講者3名・講師が画面を見て個別に支援", PALE, TEXT),
             ("データはすべて架空。実際の顧客情報は入力しない", ORANGE_PALE, ORANGE)]
    for i, (t, f, c) in enumerate(notes):
        x = X0 + i * (cw + gap)
        s.box(x, 5050000, cw, 700000, para(t, size=1250, bold=True, color=c, align="ctr"),
              fill=f, prst="roundRect", anchor="ctr")
    slides.append(s)

    # 4 研修ストーリー -----------------------------------------------------------
    s = Slide("content", "研修ストーリー：ELIソリューションズの営業として提案する")
    s.box(X0, 1030000, 2600000, 760000,
          ps([("ELIソリューションズ", {"size": 1400, "bold": True, "color": WHITE}),
              ("営業 高橋（あなた）", {"size": 1200, "color": WHITE})]),
          fill=NAVY, prst="roundRect", anchor="ctr", inset=(180000, 45720, 91440, 45720))
    s.box(X0 + 2700000, 1120000, 1150000, 580000, para("提案", size=1300, bold=True, color=WHITE, align="ctr"),
          fill=BLUE, prst="rightArrow", anchor="ctr")
    s.box(X0 + 3950000, 1030000, W - 3950000, 760000,
          ps([("みらい商事株式会社（架空・東京都・全社約300名）", {"size": 1350, "bold": True, "color": NAVY}),
              ("人材開発 佐藤様・営業企画 田中様「生成AIの利用状況に差がある」", {"size": 1150})]),
          fill=LIGHT, prst="roundRect", anchor="ctr", inset=(180000, 45720, 91440, 45720))
    chips = [("対象：法人営業20名", PALE, TEXT), ("A案 60万円／B案 100万円", PALE, TEXT),
             ("予算目安100万円（承認前）", ORANGE_PALE, ORANGE), ("利用可否・承認者などは未確定", ORANGE_PALE, ORANGE)]
    cws = [1900000, 2500000, 2350000, 2496000]
    cx = X0
    for (t, f, c), cw_ in zip(chips, cws):
        s.box(cx, 1880000, cw_ - 80000, 380000, para(t, size=1050, bold=True, color=c, align="ctr"),
              fill=f, prst="roundRect", anchor="ctr", inset=(45720, 0, 45720, 0))
        cx += cw_
    rows = [["STEP", "やること", "使うアプリ", "演習"],
            ["1", "顧客と業界を調べる", "Copilot アプリ（Web検索）", "演習3"],
            ["2", "入力してはいけない情報を取り除く", "Copilot アプリ", "演習4"],
            ["3", "ヒアリングシートを作る", "Word", "演習5"],
            ["4", "商談の文字起こしから議事録を作る", "Word", "演習6"],
            ["5", "議事録送付メール・社内報告・確認事項の一覧を作る", "Copilot アプリ／Word", "演習7・8"],
            ["6", "過去の研修実績を分析する", "Excel", "演習9"],
            ["7", "A案・B案の見積を試算する", "Excel", "演習10"],
            ["8", "A案・B案の提案書と上長説明用の1枚を書く", "Word", "演習11"],
            ["9", "上長説明用の1枚と提案スライドを作る", "PowerPoint", "演習12"],
            ["10", "自分の業務への応用を考える", "Word／Codex（任意）", "演習13・14"]]
    s.table(X0, 2360000, [800000, 4300000, 2700000, 1446000], rows, row_h=360000, size=1100,
            aligns=["ctr", "l", "l", "ctr"], fills={10: ORANGE_PALE})
    slides.append(s)

    # 5 タイムテーブル ------------------------------------------------------------
    s = Slide("content", "2日間のタイムテーブル（各日 9:30〜17:00）")
    half = (W - 200000) / 2
    day1 = [["時間", "内容"],
            ["9:30–9:50", "オリエンテーション"],
            ["9:50–10:40", "第1章 生成AIの進化と現状"],
            ["10:50–12:00", "第2章 基本操作とプロンプト（演習1〜3）"],
            ["12:00–13:00", "昼休憩"],
            ["13:00–14:00", "第3章 セキュアに使う（演習4）"],
            ["14:10–15:30", "第4章 Word：議事録ほか（演習5・6）"],
            ["15:40–16:40", "第5章 商談後フォロー（演習7・8）"],
            ["16:40–17:00", "Day1 振り返り"]]
    day2 = [["時間", "内容"],
            ["9:30–9:45", "Day1 の復習・セキュリティクイズ"],
            ["9:45–11:05", "第6章 Excel：分析・見積（演習9・10）"],
            ["11:15–12:00", "第7章 Word：提案書（演習11）"],
            ["12:00–13:00", "昼休憩"],
            ["13:00–13:45", "第8章 PowerPoint：提案スライド（演習12）"],
            ["13:45–14:30", "第9章 ELI Sales Assist の紹介"],
            ["14:40–16:20", "第10章 業務への応用（演習13・14）"],
            ["16:20–17:00", "発表・まとめ・理解度テスト"]]
    for i, (label, rows, fills) in enumerate([
            ("Day 1　生成AIの基礎と商談前後の活用", day1, {4: GRAY_FILL}),
            ("Day 2　分析・提案書作成と業務への応用", day2, {4: GRAY_FILL, 6: ORANGE_PALE, 7: ORANGE_PALE, 8: ORANGE_PALE})]):
        x = X0 + i * (half + 200000)
        s.text(x, 1030000, half, 360000, para(label, size=1400, bold=True, color=NAVY))
        s.table(x, 1430000, [1250000, half - 1250000], rows, row_h=460000, size=1050, fills=fills)
    s.box(X0, 5700000, 260000, 260000, fill=PALE, line="BBBBBB")
    s.text(X0 + 340000, 5690000, 4300000, 280000, para("パートA：基礎・セキュリティ・Office連携（約3/4）", size=1100))
    s.box(X0 + 4750000, 5700000, 260000, 260000, fill=ORANGE_PALE, line="BBBBBB")
    s.text(X0 + 5090000, 5690000, 4150000, 280000, para("パートB：自社アプリ紹介と業務への応用（約1/4）", size=1100))
    s.text(X0, 6040000, W, 280000, para("※ 各コマの間に10分の休憩があります。", size=1000, color=GRAY))
    slides.append(s)

    # 6 章扉 ---------------------------------------------------------------------
    slides.append(Slide("section", "１．生成AIの進化と現状"))

    # 7 1.1 AIの歩み ---------------------------------------------------------------
    s = Slide("content", "1.1 AIの歩み")
    rows = [["時期", "出来事", "ポイント"],
            ["1950〜60年代", "第1次AIブーム（探索・推論）", "パズルや迷路は解けるが、現実の問題には使えなかった"],
            ["1980年代", "第2次AIブーム（エキスパートシステム）", "専門家の知識をルールとして書き込む。ルールの作成・保守が限界に"],
            ["2000年代〜", "第3次AIブーム（機械学習・深層学習）", "データから規則性を自動で学ぶ。画像認識の精度が急速に向上"],
            ["2017年", "Transformer の発表", "単語同士の関係をまとめて捉える仕組み。今の生成AIの土台"],
            ["2022年11月", "ChatGPT の公開", "誰でも会話で使える生成AIが登場し、利用者が爆発的に増える"],
            ["2023年", "マルチモーダル化・業務ツールへの組み込み", "画像も理解。Microsoft 365 に Copilot が組み込まれ始める"],
            ["2024年", "推論モデルの登場", "答える前に「考える」時間を取り、複雑な問題の正答率が向上"],
            ["2025年〜", "エージェントの普及", "調べる・資料を作る・コードを書くなど、複数の手順を自律的に進める"]]
    s.table(X0, 1030000, [1500000, 3300000, W - 4800000], rows, row_h=400000, size=1100, bold_cols=(0,),
            fills={4: PALE, 5: PALE})
    s.box(X0, 4850000, W, 1380000,
          ps([("現在（2026年）", {"size": 1400, "bold": True, "color": NAVY, "space_after": 400}),
              ("生成AIは「質問に答える道具」から「仕事の一部を任せられる同僚」に近づいている。"
               "Word・Excel・PowerPoint の中から直接AIを呼び出せるようになった一方で、"
               "**AIに渡す情報と、AIが作ったものの正しさに対する人間の責任は、むしろ重くなっている。**",
               {"size": 1250, "line": 120000, "accent": NAVY})]),
          fill=LIGHT, prst="roundRect", adj={"adj": 6000}, inset=(220000, 150000, 220000, 120000))
    slides.append(s)

    # 8 1.2 LLMの仕組み --------------------------------------------------------------
    s = Slide("content", "1.2 大規模言語モデル（LLM）の仕組み")
    s.box(X0, 1030000, W, 620000,
          para("LLM ＝ それまでの文章に続く **「もっともらしい次の言葉」** を予測し続けるプログラム",
               size=1700, bold=True, color=NAVY, align="ctr", accent=ORANGE),
          fill=PALE, prst="roundRect", anchor="ctr")
    # 入力
    s.box(X0, 2250000, 3000000, 1300000,
          ps([("入力（それまでの文章）", {"size": 1100, "color": GRAY, "space_after": 300}),
              ("「お打ち合わせのお時間をいただき、誠に」", {"size": 1400, "bold": True, "line": 120000})]),
          fill=WHITE, line=BLUE, prst="roundRect", anchor="ctr", inset=(180000, 91440, 180000, 91440))
    s.box(X0 + 3120000, 2650000, 650000, 500000, fill=BLUE, prst="rightArrow")
    # 確率
    px = X0 + 3900000
    s.text(px, 1850000, W - 3900000, 330000, para("次の言葉の候補と確率（イメージ）", size=1200, bold=True, color=NAVY))
    cands = [("ありがとう", 82), ("感謝", 9), ("恐縮", 4), ("申し訳", 2), ("その他", 3)]
    bar_max = 3300000
    for i, (w_, pct) in enumerate(cands):
        y = 2230000 + i * 390000
        s.text(px, y, 1150000, 330000, para(w_, size=1200, bold=(i == 0)), anchor="ctr")
        s.box(px + 1200000, y + 40000, max(bar_max * pct / 100, 60000), 250000,
              fill=BLUE if i == 0 else LIGHT, prst="rect")
        s.text(px + 1200000 + max(bar_max * pct / 100, 60000) + 80000, y, 600000, 330000,
               para(f"{pct}%", size=1200, bold=(i == 0), color=NAVY if i == 0 else GRAY), anchor="ctr")
    # 手順
    steps = ["① 文章を読む", "② 確率を計算", "③ 1語を選ぶ", "④ 加えて繰り返す"]
    sw = (W + 120000 * 3) / 4
    for i, t in enumerate(steps):
        s.box(X0 + i * (sw - 120000), 4480000, sw, 620000, para(t, size=1200, bold=True, color=WHITE, align="ctr"),
              fill=[NAVY, BLUE, BLUE, "3A96D8"][i], prst="chevron" if i else "homePlate", anchor="ctr",
              adj={"adj": 30000}, inset=(250000, 45720, 200000, 45720))
    s.box(X0, 5300000, W, 800000,
          para("この仕組みから、**「毎回答えが変わる」「もっともらしい誤りをつくる」「計算が苦手」** といった性質が生まれる（次ページ）",
               size=1300, line=120000, accent=NAVY),
          fill=PALE, prst="roundRect", anchor="ctr", inset=(220000, 45720, 220000, 45720))
    slides.append(s)

    # 9 1.2 LLMの性質 ----------------------------------------------------------------
    s = Slide("content", "1.2 LLMの性質と業務への影響")
    rows = [["性質", "業務への影響・対応"],
            ["同じ質問でも毎回答えが少し変わる", "気に入らなければ再生成。同じ結果の再現は保証されない"],
            ["もっともらしい嘘をつくことがある（ハルシネーション）", "数字・固有名詞・日付・出典は必ず確認する"],
            ["学習した時点以降の情報を知らない", "最新情報は Web 検索機能を使い、出典を確認する"],
            ["指示（プロンプト）の質で結果が大きく変わる", "目的・前提・出力形式をはっきり伝える（第2章）"],
            ["計算や厳密な集計は苦手", "計算は Excel の数式に任せ、AIには数式を作らせる（第6章）"]]
    s.table(X0, 1030000, [4550000, W - 4550000], rows, row_h=540000, size=1250, bold_cols=(0,),
            fills={(2, 0): ORANGE_PALE})
    s.box(X0, 4480000, 5700000, 1650000,
          ps([("営業での原則", {"size": 1300, "bold": True, "color": WHITE, "space_after": 600}),
              ("AIは「下書き担当」「壁打ち相手」。", {"size": 1800, "bold": True, "color": WHITE}),
              ("最終確認と判断は、必ず人が行う。", {"size": 1800, "bold": True, "color": WHITE})]),
          fill=NAVY, prst="roundRect", anchor="ctr", inset=(250000, 91440, 250000, 91440), adj={"adj": 6000})
    s.box(X0 + 5900000, 4480000, W - 5900000, 1650000,
          ps([("必ず確認する4つ", {"size": 1300, "bold": True, "color": ORANGE, "space_after": 400}),
              *[(t, {"bullet": "check", "size": 1400, "space_before": 300}) for t in ("数字", "固有名詞", "日付・曜日", "出典")]]),
          fill=ORANGE_PALE, prst="roundRect", anchor="ctr", inset=(250000, 91440, 150000, 91440), adj={"adj": 6000})
    slides.append(s)

    # 10 ミニ演習 ---------------------------------------------------------------------
    s = Slide("content", "ミニ演習：同じ質問を聞き比べる（約5分）")
    steps = ["Copilot アプリで新しいチャットを開き、質問Aを入力する",
             "隣の人と答えを見比べる",
             "「再生成」して、もう一度比べる",
             "言い回しを変えた質問Bを入力し、答えの変化を見る"]
    for i, t in enumerate(steps):
        y = 1150000 + i * 850000
        s.circle_num(X0, y, 520000, i + 1)
        s.text(X0 + 680000, y, 3900000, 520000, para(t, size=1350, line=115000), anchor="ctr")
    rx = X0 + 4800000
    rw = W - 4800000
    s.text(rx, 1080000, rw, 330000, para("質問A", size=1200, bold=True, color=NAVY))
    s.box(rx, 1420000, rw, 620000, para("営業の仕事で一番大切なことは？", size=1350),
          fill=CODE_FILL, line="C8C8C8", anchor="ctr", inset=(160000, 45720, 160000, 45720))
    s.text(rx, 2230000, rw, 330000, para("質問B（言い回しを変える）", size=1200, bold=True, color=NAVY))
    s.box(rx, 2570000, rw, 1150000,
          para("法人向け研修の営業担当者が成果を出すために最も重要なことを1つ、理由とともに教えてください。",
               size=1350, line=120000),
          fill=CODE_FILL, line="C8C8C8", anchor="ctr", inset=(160000, 45720, 160000, 45720))
    s.box(X0, 4700000, W, 1450000,
          ps([("考えるポイント", {"size": 1400, "bold": True, "color": NAVY, "space_after": 500}),
              ("なぜ同じ質問でも答えが変わるのか？（→ 1.2 の仕組み）", {"bullet": "dot", "size": 1300}),
              ("質問Aと質問B、仕事で使いやすい答えはどちらか？ 何が違ったか？（→ 第2章 プロンプトの4要素）",
               {"bullet": "dot", "size": 1300})]),
          fill=LIGHT, prst="roundRect", anchor="ctr", inset=(250000, 91440, 250000, 91440), adj={"adj": 6000})
    slides.append(s)
    return slides


def batch2():
    slides = []

    # 11 1.3 得意・不得意 -------------------------------------------------------
    s = Slide("content", "1.3 生成AIの得意・不得意")
    rows = [["得意なこと", "苦手なこと・注意が必要なこと"],
            ["文章の下書き・言い換え・要約", "正確な事実の保証（特に数字・固有名詞）"],
            ["アイデア出し・観点の洗い出し", "最新の出来事（検索機能なしの場合）"],
            ["文章の構造化（箇条書き・表への変換）", "厳密な計算・大量データの正確な集計"],
            ["トーンの調整（丁寧・簡潔・説得的）", "顧客との関係性や社内事情をふまえた判断"],
            ["数式・コードの作成と説明", "責任を伴う最終判断"]]
    s.table(X0, 1030000, [W / 2, W / 2], rows, row_h=560000, size=1300, fills={(0, 1): ORANGE})
    s.text(X0, 4630000, W, 330000, para("営業での使い分け", size=1400, bold=True, color=NAVY))
    parts = [("AIに任せる", "下書き・要約・構造化・言い換え", BLUE), ("人が確認する", "数字・固有名詞・日付・出典", "3A96D8"),
             ("人が決める", "判断・約束・社外への送信", NAVY)]
    pw = (W + 150000 * 2) / 3
    for i, (h, b, c) in enumerate(parts):
        s.box(X0 + i * (pw - 150000), 5020000, pw, 900000,
              ps([(h, {"size": 1450, "bold": True, "color": WHITE, "align": "ctr"}),
                  (b, {"size": 1150, "color": WHITE, "align": "ctr"})]),
              fill=c, prst="chevron" if i else "homePlate", anchor="ctr", adj={"adj": 30000},
              inset=(300000, 45720, 250000, 45720))
    slides.append(s)

    # 12 1.4 Copilot の全体像と契約 ------------------------------------------------
    s = Slide("content", "1.4 Microsoft Copilot の全体像")
    s.text(X0, 1030000, W, 330000, para("使う場所", size=1400, bold=True, color=NAVY))
    places = [("Copilot アプリ", "Web・Windows・スマートフォン", "チャット形式で質問・調査・文章作成。Web 検索や、ファイル・画像の添付もできる"),
              ("Office アプリの中の Copilot", "Word・Excel・PowerPoint・Outlook など", "開いているファイルを対象に、下書き・要約・分析・スライド作成などを行う")]
    half = (W - 230000) / 2
    for i, (h, sub_, b) in enumerate(places):
        x = X0 + i * (half + 230000)
        s.box(x, 1400000, half, 1500000,
              ps([(h, {"size": 1600, "bold": True, "color": NAVY}),
                  (sub_, {"size": 1100, "color": GRAY, "space_after": 600}),
                  (b, {"size": 1250, "line": 120000})]),
              fill=PALE, prst="roundRect", adj={"adj": 8000}, inset=(220000, 150000, 220000, 120000))
    s.text(X0, 3120000, W, 330000, para("契約の種類", size=1400, bold=True, color=NAVY))
    rows = [["契約", "主な対象", "本研修での扱い"],
            ["Microsoft 365 Personal／Family", "個人・家族", "—"],
            ["Microsoft 365 Premium", "個人・家族（高い利用上限と高度な機能）", "本研修で使用"],
            ["Microsoft 365 Copilot（法人向け）", "企業・組織（職場アカウント）", "第3章で違いを比較"]]
    s.table(X0, 3490000, [3500000, 3400000, W - 6900000], rows, row_h=480000, size=1200,
            fills={2: ORANGE_PALE}, bold_cols=(0,))
    s.text(X0, 5550000, W, 500000,
           para("※ 機能名・プラン構成は変更されることがあります（2026年9月時点の情報）。当日の画面に合わせて読み替えてください。",
                size=1050, color=GRAY))
    slides.append(s)

    # 13 1.4 Premium でできること -------------------------------------------------
    s = Slide("content", "1.4 Microsoft 365 Premium でできること")
    cards = [("文", "Office アプリの Copilot", "Word・Excel・PowerPoint・Outlook で、下書き・要約・分析・スライド作成"),
             ("問", "Copilot アプリ", "Web 検索つきのチャット、ファイルの添付、じっくり考えるモード"),
             ("調", "深い調査・分析", "Researcher・Analyst など（提供状況は当日講師が確認）"),
             ("量", "高い利用上限", "Personal／Family より多く使える（上限の詳細は変わることがある）")]
    cw = (W - 230000) / 2
    for i, (icon, h, b) in enumerate(cards):
        x = X0 + (i % 2) * (cw + 230000)
        y = 1080000 + (i // 2) * 1600000
        s.box(x, y, cw, 1420000, fill=PALE, prst="roundRect", adj={"adj": 8000})
        s.circle_num(x + 220000, y + 420000, 600000, icon, size=1300 if len(icon) > 2 else 1800)
        s.text(x + 1000000, y + 230000, cw - 1150000, 420000, para(h, size=1600, bold=True, color=NAVY))
        s.text(x + 1000000, y + 680000, cw - 1150000, 650000, para(b, size=1250, line=115000))
    s.box(X0, 4400000, W, 1300000,
          ps([("ポイント：Premium は「個人向け」の契約", {"size": 1500, "bold": True, "color": ORANGE, "space_after": 500}),
              ("会社の業務データ（顧客情報・社内情報）を扱ってよいかは、契約とデータ保護の内容、そして会社のルールで決まる。"
               "本研修では **架空のデータだけ** を使い、考え方は第3章で学ぶ。", {"size": 1300, "line": 120000, "accent": ORANGE})]),
          fill=ORANGE_PALE, prst="roundRect", anchor="ctr", adj={"adj": 6000}, inset=(250000, 91440, 250000, 91440))
    slides.append(s)

    # 14 1.5 営業プロセスでの使いどころ -------------------------------------------------
    s = Slide("content", "1.5 ソリューション営業のどこで使えるか")
    stages = ["事前準備", "商談", "商談後", "提案準備", "受注後・フォロー"]
    sw = (W + 120000 * 4) / 5
    for i, t in enumerate(stages):
        s.box(X0 + i * (sw - 120000), 1030000, sw, 520000, para(t, size=1250, bold=True, color=WHITE, align="ctr"),
              fill=[NAVY, "2B6CA3", BLUE, "3A96D8", "6BB0E3"][i], prst="chevron" if i else "homePlate",
              anchor="ctr", adj={"adj": 30000}, inset=(200000, 0, 150000, 0))
    rows = [["プロセス", "Copilot の使いどころ", "演習"],
            ["事前準備", "業界動向・公開情報の調査、仮説づくり、ヒアリング項目の洗い出し", "演習3・5"],
            ["商談", "商談中は相手との会話に集中。録画・文字起こしは相手の了解を得て行う\n（例：初回訪問の冒頭で「Zoomの録画と文字起こしを残します」と伝えている）", "—"],
            ["商談後", "議事録、議事録送付メール、社内報告、Next Action と確認事項の整理", "演習6・7・8"],
            ["提案準備", "実績データの分析、概算見積、提案書（A案・B案）・上長説明用の1枚・スライド", "演習9〜12"],
            ["受注後・フォロー", "実施報告、アンケート分析、次の提案の種探し", "演習9（応用）"]]
    s.table(X0, 1750000, [1700000, W - 3100000, 1400000], rows,
            row_h=[420000, 640000, 900000, 640000, 780000, 640000], size=1200, bold_cols=(0,),
            aligns=["l", "l", "ctr"])
    slides.append(s)

    # 15 章扉 -----------------------------------------------------------------------
    slides.append(Slide("section", "２．Copilot の基本操作とプロンプト設計"))

    # 16 2.1 基本操作 -------------------------------------------------------------------
    s = Slide("content", "2.1 Copilot アプリの基本操作")
    rows = [["操作", "説明"],
            ["新しいチャット", "話題が変わったら新しいチャットを始める（前の会話の影響を受けないように）"],
            ["入力欄", "質問や指示を入力する。Shift＋Enter で改行"],
            ["応答モードの切り替え", "素早く答えるモードと、じっくり考えて答えるモードがある（名称は画面で確認）"],
            ["Web 検索と出典", "最新情報を検索して答える。**回答内の出典リンクを必ず開いて確認する**"],
            ["ファイル・画像の添付", "ファイルを読み込ませて質問できる。**添付してよい情報かを先に判断する**"],
            ["コピー・再生成・評価", "回答のコピー、別の回答の生成、良し悪しのフィードバック"],
            ["履歴", "過去のチャットを開き直す・削除する"]]
    s.table(X0, 1030000, [2600000, W - 2600000], rows, row_h=520000, size=1250, bold_cols=(0,),
            fills={(4, 0): ORANGE_PALE, (5, 0): ORANGE_PALE})
    s.box(X0, 5320000, W, 700000,
          para("オレンジの2つはセキュリティに直結する操作。**出典の確認** と **添付前の判断** は第3章でくわしく扱う。",
               size=1250, accent=ORANGE),
          fill=ORANGE_PALE, prst="roundRect", anchor="ctr", inset=(220000, 45720, 220000, 45720))
    slides.append(s)

    # 17 2.2 Office で使う前提 ---------------------------------------------------------------
    s = Slide("content", "2.2 Office アプリで Copilot を使う前提")
    steps = [("OneDrive に保存", "自動保存をオンにする。ローカル保存のままだと使えない場合がある"),
             ("サインイン", "Office に、Premium の Microsoft アカウントでサインインしている"),
             ("Copilot を呼び出す", "リボンの Copilot ボタン、または文書内の Copilot アイコンから")]
    cw = (W - 2 * 230000) / 3
    for i, (h, b) in enumerate(steps):
        x = X0 + i * (cw + 230000)
        s.box(x, 1080000, cw, 1750000, fill=PALE, prst="roundRect", adj={"adj": 8000})
        s.circle_num(x + 200000, 1230000, 520000, i + 1)
        s.text(x + 800000, 1230000, cw - 900000, 520000, para(h, size=1500, bold=True, color=NAVY), anchor="ctr")
        s.text(x + 200000, 1880000, cw - 400000, 900000, para(b, size=1200, line=115000))
    s.text(X0, 3060000, W, 330000, para("本研修で使うアプリと主な使い方", size=1400, bold=True, color=NAVY))
    apps = [("Word", "ヒアリングシート、議事録、議事録送付メール、提案書（第4・5・7章）"),
            ("Excel", "研修実績データの分析、A案・B案の概算見積（第6章）"),
            ("PowerPoint", "上長説明用の1枚、提案スライド（第8章）")]
    for i, (a_, b) in enumerate(apps):
        y = 3450000 + i * 560000
        s.box(X0, y, 1700000, 460000, para(a_, size=1300, bold=True, color=WHITE, align="ctr"),
              fill=[BLUE, "2E8B57", "C55A11"][i], prst="roundRect", anchor="ctr")
        s.text(X0 + 1850000, y, W - 1850000, 460000, para(b, size=1250), anchor="ctr")
    s.box(X0, 5150000, W, 950000,
          ps([("Copilot ボタンが押せないときは", {"size": 1200, "bold": True, "color": ORANGE}),
              ("OneDrive に保存されているか → 自動保存がオンか → サインインしているアカウント → （Excel）データがテーブルになっているか",
               {"size": 1150})]),
          fill=ORANGE_PALE, prst="roundRect", anchor="ctr", inset=(220000, 45720, 220000, 45720))
    slides.append(s)

    # 18 2.3 プロンプトの4要素 -------------------------------------------------------------------
    s = Slide("content", "2.3 伝わるプロンプトの4要素")
    rows = [["要素", "内容", "例"],
            ["役割", "AIにどの立場で考えてほしいか", "あなたは法人向け研修の提案に詳しい営業コンサルタントです"],
            ["目的", "何のために、何を作ってほしいか", "初回訪問で聞くべき質問を洗い出したい"],
            ["前提・制約", "背景、相手、条件、してほしくないこと", "顧客は商社の人材開発担当者。所要時間は60分。予算と決裁の進め方の質問は最後に"],
            ["出力形式", "形式・分量・構成", "目的別に5つの分類で、各3問、表形式で"]]
    s.table(X0, 1030000, [1700000, 3000000, W - 4700000], rows, row_h=[440000, 720000, 720000, 820000, 720000],
            size=1250, bold_cols=(0,))
    s.box(X0, 4700000, W, 1350000,
          ps([("Microsoft の推奨も同じ考え方", {"size": 1350, "bold": True, "color": NAVY, "space_after": 500}),
              ("目的（Goal）・背景（Context）・情報源（Source）・期待（Expectations）の4つを伝える。"
               "言い方は違っても、**「何のために・どんな前提で・何を見て・どんな形で」** を伝えることが大切。",
               {"size": 1250, "line": 120000, "accent": NAVY})]),
          fill=LIGHT, prst="roundRect", anchor="ctr", adj={"adj": 6000}, inset=(250000, 91440, 250000, 91440))
    slides.append(s)

    # 19 2.3 悪い例・良い例 --------------------------------------------------------------------
    s = Slide("content", "2.3 悪い例と良い例")
    s.box(X0, 1080000, 2500000, 4900000,
          ps([("× 悪い例", {"size": 1500, "bold": True, "color": ORANGE, "space_after": 800}),
              ("研修の提案書を書いて", {"size": 1500, "bold": True, "space_after": 1200}),
              ("足りないもの", {"size": 1200, "bold": True, "color": GRAY, "space_after": 300}),
              *[(t, {"size": 1200, "bullet": "dot", "color": GRAY}) for t in ("誰の立場で？", "何のために？", "どんな前提で？", "どんな形で？")],
              ("", {"size": 1200, "space_after": 800}),
              ("結果", {"size": 1200, "bold": True, "color": GRAY, "space_after": 300}),
              ("誰にでも当てはまる一般論の長文が返り、結局ほとんど書き直すことになる", {"size": 1200, "line": 115000})]),
          fill=ORANGE_PALE, prst="roundRect", adj={"adj": 6000}, inset=(220000, 220000, 200000, 150000))
    rx = X0 + 2700000
    rw = W - 2700000
    s.text(rx, 1080000, rw, 380000, para("○ 良い例", size=1500, bold=True, color=BLUE))
    parts = [("役割", "あなたは法人研修の提案経験が豊富な営業担当者です。"),
             ("目的", "法人営業向け生成AI研修の提案書のうち、「課題認識」（お客様の課題を整理する部分）の文章を作りたいです。読み手は商社の人材開発担当者です。"),
             ("前提", "ヒアリングで分かった課題は3点：①生成AIの利用状況に個人差が大きい　②提案資料と議事録の作成に時間がかかっている　③顧客情報を入力してよいのか不安が大きい"),
             ("出力形式", "顧客の言葉を活かし、各課題を2〜3文で。見出しつきの箇条書きで、全体で400字程度。")]
    heights = [620000, 900000, 1350000, 900000]
    y = 1520000
    for (lab, t), h in zip(parts, heights):
        s.box(rx, y, 1150000, h - 90000, para(lab, size=1200, bold=True, color=WHITE, align="ctr"),
              fill=BLUE, prst="roundRect", anchor="ctr", inset=(0, 0, 0, 0))
        s.box(rx + 1250000, y, rw - 1250000, h - 90000, para(t, size=1200, line=115000),
              fill=CODE_FILL, line="C8C8C8", anchor="ctr", inset=(150000, 45720, 150000, 45720))
        y += h
    s.text(rx, y + 60000, rw, 330000,
           para("※ 社名・氏名は入れていない（入力してよい情報の判断は第3章）", size=1050, color=GRAY))
    slides.append(s)

    # 20 2.4 6つのコツ ----------------------------------------------------------------------------
    s = Slide("content", "2.4 対話で結果を良くする6つのコツ")
    tips = [("一度で完璧を求めない", "まず出させてから「もっと短く」「表にして」と直す"),
            ("例を見せる", "「この書き方を参考に」と見本を貼る（見本に機密情報がないか確認）"),
            ("分けて頼む", "「構成案 → 確認 → 本文」の順に進める"),
            ("評価の観点を与える", "「顧客の立場で読んで、分かりにくい点を3つ指摘して」"),
            ("分からないと言わせる", "「根拠がない場合は“不明”と書いてください」"),
            ("確認させる", "「今の回答で事実確認が必要な箇所を挙げてください」")]
    cw = (W - 2 * 200000) / 3
    ch = 1650000
    for i, (h, b) in enumerate(tips):
        x = X0 + (i % 3) * (cw + 200000)
        y = 1080000 + (i // 3) * (ch + 200000)
        s.box(x, y, cw, ch, fill=PALE, prst="roundRect", adj={"adj": 8000})
        s.circle_num(x + 180000, y + 200000, 480000, i + 1)
        s.text(x + 760000, y + 200000, cw - 850000, 480000, para(h, size=1400, bold=True, color=NAVY), anchor="ctr")
        s.text(x + 180000, y + 850000, cw - 360000, ch - 950000, para(b, size=1250, line=120000))
    s.box(X0, 4700000, W, 1250000,
          ps([("基本の流れ", {"size": 1350, "bold": True, "color": NAVY, "space_after": 400}),
              ("**まず出させる → 足りない点を追加で指示する → 事実確認が必要な箇所を挙げさせる → 人が最終確認する**",
               {"size": 1300, "accent": NAVY}),
              ("会話が長くなって話がずれてきたら、要点をまとめて新しいチャットで始め直す", {"size": 1150, "color": GRAY})]),
          fill=LIGHT, prst="roundRect", anchor="ctr", adj={"adj": 6000}, inset=(250000, 91440, 250000, 91440))
    slides.append(s)
    return slides


BATCHES = [batch1, batch2]


def main():
    slides = [s for b in BATCHES for s in b()]
    build(TEMPLATE, slides, OUT)
    print(f"{OUT.relative_to(ROOT)}（{len(slides)}枚）")


if __name__ == "__main__":
    main()
