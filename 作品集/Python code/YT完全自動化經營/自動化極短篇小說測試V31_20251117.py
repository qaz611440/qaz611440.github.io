import os
import json
import re
import random
import shutil
from dotenv import load_dotenv
from openai import OpenAI
from deep_translator import GoogleTranslator
import time
import uuid
import asyncio
import requests

# ==============================================================================
# --- 常數設定 ---
# ==============================================================================
BASE_OUTPUT_DIR = r"D:\python_store_folder\youtube_video_story"
TITLES_FILE_PATH = r"D:\已上傳YT的小說書名\uploaded_novel_titles.txt"
AI_MODEL = "grok-4-fast-reasoning-latest"

# ==============================================================================
# --- 輔助函數 ---
# ==============================================================================

def translate_english_parts(text, translator, retries=5):
    """將文本中的英文部分翻譯為目標語言，保留所有格和縮寫"""
    for attempt in range(retries):
        try:
            english_parts = re.findall(r'\b[a-zA-Z][a-zA-Z\'-]*[a-zA-Z]\b', text)
            if not english_parts:
                return text
            
            translated_text = text
            detected_parts = set(p for p in english_parts if "'" not in p) 
            
            for part in detected_parts:
                if len(part) > 2 or not part.isupper():
                    translated = translator.translate(part)
                    if translated and translated.lower() != part.lower():
                        translated_text = re.sub(r'\b' + re.escape(part) + r'\b', translated, translated_text)
            return translated_text
        except Exception as e:
            print(f"翻譯文本時出錯（嘗試 {attempt+1}/{retries}）：{e}")
            if attempt == retries - 1:
                print("翻譯失敗，將保留原始文本。")
                return text
            time.sleep(2)

def translate_json_data(json_data, target_lang, retries=5):
    """將 JSON 數據翻譯為目標語言"""
    translator = GoogleTranslator(source='zh-TW', target=target_lang)
    translated_data = {}
    for key, value in json_data.items():
        for attempt in range(retries):
            try:
                if isinstance(value, str) and key not in ["novel_playlist_title", "novel_playlist_description"]:
                    translated_data[key] = translator.translate(value)
                elif isinstance(value, list):
                    translated_data[key] = [translator.translate(str(item)) for item in value]
                else:
                    translated_data[key] = value
                break
            except Exception as e:
                print(f"翻譯 JSON 欄位 '{key}' 時出錯（嘗試 {attempt+1}/{retries}）：{e}")
                if attempt == retries - 1:
                    translated_data[key] = value
                time.sleep(2)
    return translated_data


# ==============================================================================
# --- 生成 user_prompt_config ---
# ==============================================================================

def generate_user_prompt_config(client, output_dir):
    """
    生成隨機化的 user_prompt_config，聚焦短篇爽感小說，簡化結構，無範例。
    """
    MAIN_GENRES = [
        "懸疑推理", "網遊", "星際", "機甲", "異世界", "搞笑", "恐怖", "都市異能", "末日求生", "都市修仙", "霸道總裁", "青春", "輕小說"
    ]

    GENRE_SPECIFIC_KEYWORDS= {
        "懸疑推理": [
            # 核心主題
            {"keyword": "深夜連環殺殺人案的追蹤", "type": "核心主題"},
            {"keyword": "失蹤人口的隱秘線索", "type": "核心主題"},
            {"keyword": "詭異密室謀殺的解謎", "type": "核心主題"},
            {"keyword": "心理變態兇手的對決", "type": "核心主題"},
            {"keyword": "古宅鬼影的調查真相", "type": "核心主題"},
            {"keyword": "間諜陰謀的國際追捕", "type": "核心主題"},
            {"keyword": "病毒爆發的源頭追查", "type": "核心主題"},
            {"keyword": "失憶者的身份危機", "type": "核心主題"},
            {"keyword": "詐騙集團的內部臥底", "type": "核心主題"},
            {"keyword": "預言殺人的先知謎團", "type": "核心主題"},
            {"keyword": "家族詛咒的世代秘密", "type": "核心主題"},
            {"keyword": "黑市器官交易的揭露", "type": "核心主題"},
            {"keyword": "黑市器官交易的揭露", "type": "核心主題"},
            {"keyword": "時間悖論的因果追蹤", "type": "核心主題"},
            {"keyword": "名人綁架案的贖金陰謀", "type": "核心主題"},
            {"keyword": "藝術品盜竊的幕後黑手", "type": "核心主題"},
            {"keyword": "靈異事件的科學解釋", "type": "核心主題"},
            {"keyword": "政治暗殺的證據蒐集", "type": "核心主題"},
            {"keyword": "夢境兇案的潛意識探查", "type": "核心主題"},
            {"keyword": "地下賭場的作弊曝光", "type": "核心主題"},
            {"keyword": "雙重人格的犯罪剖析", "type": "核心主題"},
            {"keyword": "海洋沉船的寶藏謎題", "type": "核心主題"},
            # 輔助元素
            {"keyword": "隱藏的日記線索", "type": "輔助元素"},
            {"keyword": "監控錄像的細節", "type": "輔助元素"},
            {"keyword": "目擊證人的證詞", "type": "輔助元素"},
            {"keyword": "法醫報告的異常", "type": "輔助元素"},
            {"keyword": "匿名信件的威脅", "type": "輔助元素"},
            {"keyword": "血跡分析的結果", "type": "輔助元素"},
            {"keyword": "手機記錄的通話", "type": "輔助元素"},
            {"keyword": "密碼鎖定的文件", "type": "輔助元素"},
            {"keyword": "偽造的證件身份", "type": "輔助元素"},
            {"keyword": "意外的目擊者", "type": "輔助元素"},
            {"keyword": "心理測試的結果", "type": "輔助元素"},
            {"keyword": "舊照片的秘密", "type": "輔助元素"},
            {"keyword": "指紋比對的匹配", "type": "輔助元素"},
            {"keyword": "監聽裝置的錄音", "type": "輔助元素"},
            {"keyword": "地圖上的標記", "type": "輔助元素"},
            {"keyword": "毒物檢測的報告", "type": "輔助元素"},
            {"keyword": "逃亡者的足跡", "type": "輔助元素"},
            {"keyword": "黑客入侵的數據", "type": "輔助元素"},
            {"keyword": "詭異符號的解讀", "type": "輔助元素"},
            {"keyword": "失蹤者的物品", "type": "輔助元素"},
            {"keyword": "嫌疑人的不在場證明", "type": "輔助元素"},
            {"keyword": "隱秘會面的記錄", "type": "輔助元素"}
        ],
        "網遊": [
            # 核心主題
            {"keyword": "隱藏職業的覺醒冒險", "type": "核心主題"},
            {"keyword": "公會戰爭的領袖崛起", "type": "核心主題"},
            {"keyword": "虛擬世界的現實入侵", "type": "核心主題"},
            {"keyword": "寵物系統的極限養成", "type": "核心主題"},
            {"keyword": "副本挑戰的團隊合作", "type": "核心主題"},
            {"keyword": "裝備打造的匠師傳奇", "type": "核心主題"},
            {"keyword": "競技場的冠軍之路", "type": "核心主題"},
            {"keyword": "遊戲bug的意外收穫", "type": "核心主題"},
            {"keyword": "跨服戰鬥的英雄對決", "type": "核心主題"},
            {"keyword": "NPC叛變的劇情轉折", "type": "核心主題"},
            {"keyword": "經濟系統的商戰博弈", "type": "核心主題"},
            {"keyword": "任務鏈的史詩故事", "type": "核心主題"},
            {"keyword": "結婚系統的浪漫支線", "type": "核心主題"},
            {"keyword": "升級狂人的極速成長", "type": "核心主題"},
            {"keyword": "隱藏地圖的探索發現", "type": "核心主題"},
            {"keyword": "技能融合的創新戰鬥", "type": "核心主題"},
            {"keyword": "遊戲更新的危機事件", "type": "核心主題"},
            {"keyword": "職業轉職的命運選擇", "type": "核心主題"},
            {"keyword": "世界boss的集結討伐", "type": "核心主題"},
            {"keyword": "玩家互動的友情羈絆", "type": "核心主題"},
            {"keyword": "遊戲內的懸疑推理", "type": "核心主題"},
            {"keyword": "虛擬貨幣的現實兌換", "type": "核心主題"},
            # 輔助元素
            {"keyword": "稀有裝備的掉落", "type": "輔助元素"},
            {"keyword": "技能書的獲取", "type": "輔助元素"},
            {"keyword": "公會徽章的設計", "type": "輔助元素"},
            {"keyword": "寵物蛋的孵化", "type": "輔助元素"},
            {"keyword": "副本門票的兌換", "type": "輔助元素"},
            {"keyword": "競技積分的排名", "type": "輔助元素"},
            {"keyword": "bug報告的獎勵", "type": "輔助元素"},
            {"keyword": "跨服傳送的門戶", "type": "輔助元素"},
            {"keyword": "NPC對話的選項", "type": "輔助元素"},
            {"keyword": "拍賣行的競價", "type": "輔助元素"},
            {"keyword": "任務道具的收集", "type": "輔助元素"},
            {"keyword": "婚禮儀式的舉行", "type": "輔助元素"},
            {"keyword": "經驗藥水的服用", "type": "輔助元素"},
            {"keyword": "隱藏寶箱的開啟", "type": "輔助元素"},
            {"keyword": "技能樹的點亮", "type": "輔助元素"},
            {"keyword": "更新公告的閱讀", "type": "輔助元素"},
            {"keyword": "轉職試煉的挑戰", "type": "輔助元素"},
            {"keyword": "boss技能的閃避", "type": "輔助元素"},
            {"keyword": "好友列表的添加", "type": "輔助元素"},
            {"keyword": "推理事件的證據", "type": "輔助元素"},
            {"keyword": "貨幣兌換的匯率", "type": "輔助元素"},
            {"keyword": "遊戲頭盔的連接", "type": "輔助元素"}
        ],
        "星際": [
            # 核心主題
            {"keyword": "外星殖民的開拓之旅", "type": "核心主題"},
            {"keyword": "宇宙戰艦的艦長傳奇", "type": "核心主題"},
            {"keyword": "黑洞探險的未知危機", "type": "核心主題"},
            {"keyword": "星際聯盟的和平守護", "type": "核心主題"},
            {"keyword": "蟲洞穿越的時空冒險", "type": "核心主題"},
            {"keyword": "外星種族的交流融合", "type": "核心主題"},
            {"keyword": "能源危機的科技突破", "type": "核心主題"},
            {"keyword": "叛軍起義的星際革命", "type": "核心主題"},
            {"keyword": "太空站的生存挑戰", "type": "核心主題"},
            {"keyword": "量子通訊的秘密解碼", "type": "核心主題"},
            {"keyword": "行星改造的生態工程", "type": "核心主題"},
            {"keyword": "銀河巡邏的邊境衝突", "type": "核心主題"},
            {"keyword": "人工智能的覺醒叛變", "type": "核心主題"},
            {"keyword": "星際貿易的商業帝國", "type": "核心主題"},
            {"keyword": "宇宙病毒的疫情控制", "type": "核心主題"},
            {"keyword": "光速航行的速度競賽", "type": "核心主題"},
            {"keyword": "外星遺跡的考古發現", "type": "核心主題"},
            {"keyword": "星球毀滅的逃亡計劃", "type": "核心主題"},
            {"keyword": "多維空間的探索奧秘", "type": "核心主題"},
            {"keyword": "克隆技術的倫理困境", "type": "核心主題"},
            {"keyword": "星際戰爭的英雄傳說", "type": "核心主題"},
            {"keyword": "虛擬現實的宇宙模擬", "type": "核心主題"},
            # 輔助元素
            {"keyword": "激光武器的射擊", "type": "輔助元素"},
            {"keyword": "防護盾的能量", "type": "輔助元素"},
            {"keyword": "航行日誌的記錄", "type": "輔助元素"},
            {"keyword": "外星語言的翻譯", "type": "輔助元素"},
            {"keyword": "能源晶體的採集", "type": "輔助元素"},
            {"keyword": "叛軍基地的潛入", "type": "輔助元素"},
            {"keyword": "太空艙的維修", "type": "輔助元素"},
            {"keyword": "量子訊號的接收", "type": "輔助元素"},
            {"keyword": "生態艙的植物", "type": "輔助元素"},
            {"keyword": "巡邏艦的警報", "type": "輔助元素"},
            {"keyword": "AI助手的對話", "type": "輔助元素"},
            {"keyword": "貿易站的交易", "type": "輔助元素"},
            {"keyword": "病毒樣本的分析", "type": "輔助元素"},
            {"keyword": "光速引擎的啟動", "type": "輔助元素"},
            {"keyword": "遺跡符文的解讀", "type": "輔助元素"},
            {"keyword": "逃生艙的發射", "type": "輔助元素"},
            {"keyword": "維度門的穿越", "type": "輔助元素"},
            {"keyword": "克隆體的覺醒", "type": "輔助元素"},
            {"keyword": "戰艦炮火的轟擊", "type": "輔助元素"},
            {"keyword": "模擬訓練的場景", "type": "輔助元素"},
            {"keyword": "星圖的導航", "type": "輔助元素"},
            {"keyword": "通訊干擾的破解", "type": "輔助元素"}
        ],
        "機甲": [
            # 核心主題
            {"keyword": "機甲駕駛員的成長戰鬥", "type": "核心主題"},
            {"keyword": "巨型機甲的都市防衛", "type": "核心主題"},
            {"keyword": "外星入侵的機甲抵抗", "type": "核心主題"},
            {"keyword": "機甲競賽的冠軍爭奪", "type": "核心主題"},
            {"keyword": "改造機甲的技術革新", "type": "核心主題"},
            {"keyword": "叛變機甲的內部危機", "type": "核心主題"},
            {"keyword": "地下機甲格鬥的地下世界", "type": "核心主題"},
            {"keyword": "機甲軍團的戰場指揮", "type": "核心主題"},
            {"keyword": "遺失機甲的尋找冒險", "type": "核心主題"},
            {"keyword": "機甲與駕駛員的同步融合", "type": "核心主題"},
            {"keyword": "末日機甲的生存求生", "type": "核心主題"},
            {"keyword": "機甲設計師的創新發明", "type": "核心主題"},
            {"keyword": "跨星球的機甲遠征", "type": "核心主題"},
            {"keyword": "機甲病毒的數字感染", "type": "核心主題"},
            {"keyword": "古代機甲的復活傳說", "type": "核心主題"},
            {"keyword": "機甲聯盟的和平維護", "type": "核心主題"},
            {"keyword": "個人機甲的定制戰鬥", "type": "核心主題"},
            {"keyword": "機甲學校的學員訓練", "type": "核心主題"},
            {"keyword": "隱形機甲的潛行任務", "type": "核心主題"},
            {"keyword": "機甲大戰的史詩對決", "type": "核心主題"},
            {"keyword": "能源核心的機甲升級", "type": "核心主題"},
            {"keyword": "機甲廢墟的探索發現", "type": "核心主題"},
            # 輔助元素
            {"keyword": "機甲手臂的機械臂", "type": "輔助元素"},
            {"keyword": "能量炮的發射", "type": "輔助元素"},
            {"keyword": "駕駛艙的控制面板", "type": "輔助元素"},
            {"keyword": "競賽賽道的障礙", "type": "輔助元素"},
            {"keyword": "改造零件的安裝", "type": "輔助元素"},
            {"keyword": "叛變信號的干擾", "type": "輔助元素"},
            {"keyword": "格鬥擂台的燈光", "type": "輔助元素"},
            {"keyword": "軍團旗幟的飄揚", "type": "輔助元素"},
            {"keyword": "遺失信標的定位", "type": "輔助元素"},
            {"keyword": "同步率的測試", "type": "輔助元素"},
            {"keyword": "生存裝備的補給", "type": "輔助元素"},
            {"keyword": "發明藍圖的繪製", "type": "輔助元素"},
            {"keyword": "遠征艦隊的集結", "type": "輔助元素"},
            {"keyword": "病毒代碼的刪除", "type": "輔助元素"},
            {"keyword": "古代符文的激活", "type": "輔助元素"},
            {"keyword": "聯盟會議的討論", "type": "輔助元素"},
            {"keyword": "定制塗裝的選擇", "type": "輔助元素"},
            {"keyword": "訓練模擬的場景", "type": "輔助元素"},
            {"keyword": "隱形模式的啟動", "type": "輔助元素"},
            {"keyword": "對決武器的選擇", "type": "輔助元素"},
            {"keyword": "核心替換的過程", "type": "輔助元素"},
            {"keyword": "廢墟地圖的導航", "type": "輔助元素"}
        ],
        "異世界": [
            # 核心主題
            {"keyword": "召喚勇者的魔王討伐", "type": "核心主題"},
            {"keyword": "轉生史萊姆的領地建設", "type": "核心主題"},
            {"keyword": "魔法學院的學徒生活", "type": "核心主題"},
            {"keyword": "冒險公會的任務挑戰", "type": "核心主題"},
            {"keyword": "神賜祝福的成長之路", "type": "核心主題"},
            {"keyword": "迷宮探索的寶藏獵人", "type": "核心主題"},
            {"keyword": "種族聯盟的戰爭危機", "type": "核心主題"},
            {"keyword": "料理大師的異界美食", "type": "核心主題"},
            {"keyword": "鍛造師的武器打造", "type": "核心主題"},
            {"keyword": "召喚獸的馴服大師", "type": "核心主題"},
            {"keyword": "王國公主的逃亡冒險", "type": "核心主題"},
            {"keyword": "時間迴圈的輪迴解謎", "type": "核心主題"},
            {"keyword": "隱藏村落的守護者", "type": "核心主題"},
            {"keyword": "預言書的命運指引", "type": "核心主題"},
            {"keyword": "異界商人的貿易帝國", "type": "核心主題"},
            {"keyword": "龍騎士的空中戰鬥", "type": "核心主題"},
            {"keyword": "精靈森林的生態守護", "type": "核心主題"},
            {"keyword": "亡靈法師的軍團召喚", "type": "核心主題"},
            {"keyword": "神器收集的史詩旅程", "type": "核心主題"},
            {"keyword": "異世界轉生的系統加持", "type": "核心主題"},
            {"keyword": "冒險者的日常委託", "type": "核心主題"},
            {"keyword": "魔法禁地的探險禁忌", "type": "核心主題"},
            # 輔助元素
            {"keyword": "魔法卷軸的施放", "type": "輔助元素"},
            {"keyword": "冒險卡片的註冊", "type": "輔助元素"},
            {"keyword": "祝福儀式的進行", "type": "輔助元素"},
            {"keyword": "迷宮陷阱的閃避", "type": "輔助元素"},
            {"keyword": "聯盟會議的決議", "type": "輔助元素"},
            {"keyword": "美食配方的研發", "type": "輔助元素"},
            {"keyword": "武器藍圖的繪製", "type": "輔助元素"},
            {"keyword": "召喚契約的簽訂", "type": "輔助元素"},
            {"keyword": "逃亡路線的規劃", "type": "輔助元素"},
            {"keyword": "迴圈記憶的保留", "type": "輔助元素"},
            {"keyword": "村落結界的強化", "type": "輔助元素"},
            {"keyword": "預言詩句的解讀", "type": "輔助元素"},
            {"keyword": "貿易貨物的運輸", "type": "輔助元素"},
            {"keyword": "龍鞍的裝備", "type": "輔助元素"},
            {"keyword": "森林精靈的對話", "type": "輔助元素"},
            {"keyword": "亡靈骷髏的指揮", "type": "輔助元素"},
            {"keyword": "神器碎片的收集", "type": "輔助元素"},
            {"keyword": "系統面板的查看", "type": "輔助元素"},
            {"keyword": "委託看板的選擇", "type": "輔助元素"},
            {"keyword": "禁地封印的打破", "type": "輔助元素"},
            {"keyword": "魔法元素的感知", "type": "輔助元素"},
            {"keyword": "轉生回憶的閃現", "type": "輔助元素"}
        ],
        "搞笑": [
            # 核心主題
            {"keyword": "笨拙勇者的搞笑冒險", "type": "核心主題"},
            {"keyword": "系統故障的吐槽日常", "type": "核心主題"},
            {"keyword": "魔王退休的休閒生活", "type": "核心主題"},
            {"keyword": "寵物變身的荒唐事件", "type": "核心主題"},
            {"keyword": "魔法失控的爆笑場面", "type": "核心主題"},
            {"keyword": "公會成員的沙雕互動", "type": "核心主題"},
            {"keyword": "穿越者的文化衝突", "type": "核心主題"},
            {"keyword": "假裝高手的尷尬時刻", "type": "核心主題"},
            {"keyword": "美食比賽的失敗料理", "type": "核心主題"},
            {"keyword": "戀愛喜劇的誤會連環", "type": "核心主題"},
            {"keyword": "怪物友好的和平村落", "type": "核心主題"},
            {"keyword": "超能力者的失控能力", "type": "核心主題"},
            {"keyword": "時間旅行的悖論搞笑", "type": "核心主題"},
            {"keyword": "偵探推理的荒謬結論", "type": "核心主題"},
            {"keyword": "機器人的情感BUG", "type": "核心主題"},
            {"keyword": "學校生活的惡作劇", "type": "核心主題"},
            {"keyword": "家庭聚會的混亂場面", "type": "核心主題"},
            {"keyword": "職場菜鳥的烏龍事件", "type": "核心主題"},
            {"keyword": "動物對話的奇葩對話", "type": "核心主題"},
            {"keyword": "超級英雄的平凡煩惱", "type": "核心主題"},
            {"keyword": "遊戲世界的bug濫用", "type": "核心主題"},
            {"keyword": "仙俠世界的現代梗", "type": "核心主題"},
            # 輔助元素
            {"keyword": "滑稽的跌倒場面", "type": "輔助元素"},
            {"keyword": "吐槽旁白的介入", "type": "輔助元素"},
            {"keyword": "魔王茶杯的意外", "type": "輔助元素"},
            {"keyword": "寵物台詞的搞笑", "type": "輔助元素"},
            {"keyword": "魔法爆炸的特效", "type": "輔助元素"},
            {"keyword": "成員昵稱的調侃", "type": "輔助元素"},
            {"keyword": "文化誤解的對話", "type": "輔助元素"},
            {"keyword": "假裝失敗的尷尬", "type": "輔助元素"},
            {"keyword": "料理黑洞的成品", "type": "輔助元素"},
            {"keyword": "誤會升級的劇情", "type": "輔助元素"},
            {"keyword": "怪物茶會的邀請", "type": "輔助元素"},
            {"keyword": "能力反噬的效果", "type": "輔助元素"},
            {"keyword": "悖論循環的重複", "type": "輔助元素"},
            {"keyword": "推理錯誤的結論", "type": "輔助元素"},
            {"keyword": "機器舞蹈的故障", "type": "輔助元素"},
            {"keyword": "惡作劇道具的使用", "type": "輔助元素"},
            {"keyword": "家庭爭執的化解", "type": "輔助元素"},
            {"keyword": "烏龍報告的呈現", "type": "輔助元素"},
            {"keyword": "動物吐槽的內心", "type": "輔助元素"},
            {"keyword": "英雄披風的卡住", "type": "輔助元素"},
            {"keyword": "bug重生的循環", "type": "輔助元素"},
            {"keyword": "現代科技的仙俠應用", "type": "輔助元素"}
        ],
        "恐怖": [
            # 核心主題
            {"keyword": "幽靈屋的深夜探險", "type": "核心主題"},
            {"keyword": "詛咒人偶的復仇故事", "type": "核心主題"},
            {"keyword": "森林深處的怪異生物", "type": "核心主題"},
            {"keyword": "鏡中世界的倒影惡靈", "type": "核心主題"},
            {"keyword": "醫院鬧鬼的醫療恐怖", "type": "核心主題"},
            {"keyword": "古墓探險的亡靈覺醒", "type": "核心主題"},
            {"keyword": "夢魘循環的心理折磨", "type": "核心主題"},
            {"keyword": "病毒變異的活屍末日", "type": "核心主題"},
            {"keyword": "學校傳說的靈異事件", "type": "核心主題"},
            {"keyword": "酒店房的詭異客人", "type": "核心主題"},
            {"keyword": "地下隧道的黑暗怪物", "type": "核心主題"},
            {"keyword": "預知死亡的致命幻覺", "type": "核心主題"},
            {"keyword": "家庭秘密的血腥真相", "type": "核心主題"},
            {"keyword": "海洋深淵的未知恐懼", "type": "核心主題"},
            {"keyword": "遊樂園的詛咒遊戲", "type": "核心主題"},
            {"keyword": "電子設備的鬼魂附身", "type": "核心主題"},
            {"keyword": "荒廢城市的生存驚悚", "type": "核心主題"},
            {"keyword": "時間靜止的詭異小鎮", "type": "核心主題"},
            {"keyword": "人體實驗的變態科學", "type": "核心主題"},
            {"keyword": "靈媒召喚的失控惡靈", "type": "核心主題"},
            {"keyword": "鏡子迷宮的無限恐懼", "type": "核心主題"},
            {"keyword": "夜晚公路的幽靈搭車", "type": "核心主題"},
            # 輔助元素
            {"keyword": "吱嘎作響的木門", "type": "輔助元素"},
            {"keyword": "人偶眼睛的轉動", "type": "輔助元素"},
            {"keyword": "森林霧氣的瀰漫", "type": "輔助元素"},
            {"keyword": "鏡子裂紋的擴散", "type": "輔助元素"},
            {"keyword": "醫院走廊的迴音", "type": "輔助元素"},
            {"keyword": "墓碑文字的變化", "type": "輔助元素"},
            {"keyword": "夢境重複的場景", "type": "輔助元素"},
            {"keyword": "活屍咆哮的聲音", "type": "輔助元素"},
            {"keyword": "學校鐘聲的異響", "type": "輔助元素"},
            {"keyword": "酒店門鈴的響起", "type": "輔助元素"},
            {"keyword": "隧道燈光的閃爍", "type": "輔助元素"},
            {"keyword": "幻覺影像的浮現", "type": "輔助元素"},
            {"keyword": "家庭相冊的詭異", "type": "輔助元素"},
            {"keyword": "深海水壓的壓迫", "type": "輔助元素"},
            {"keyword": "遊樂設施的失控", "type": "輔助元素"},
            {"keyword": "手機訊號的干擾", "type": "輔助元素"},
            {"keyword": "城市廢墟的崩塌", "type": "輔助元素"},
            {"keyword": "鐘錶指針的靜止", "type": "輔助元素"},
            {"keyword": "實驗儀器的運轉", "type": "輔助元素"},
            {"keyword": "召喚蠟燭的熄滅", "type": "輔助元素"},
            {"keyword": "迷宮反射的影子", "type": "輔助元素"},
            {"keyword": "公路霧燈的閃爍", "type": "輔助元素"}
        ],
        "都市異能": [
            # 核心主題
            {"keyword": "隱藏超能力的都市生活", "type": "核心主題"},
            {"keyword": "讀心術者的職場逆襲", "type": "核心主題"},
            {"keyword": "時間操控的犯罪對抗", "type": "核心主題"},
            {"keyword": "隱形能力的偷竊冒險", "type": "核心主題"},
            {"keyword": "預知未來的彩票中獎", "type": "核心主題"},
            {"keyword": "動物溝通的寵物偵探", "type": "核心主題"},
            {"keyword": "瞬間移動的逃亡追逐", "type": "核心主題"},
            {"keyword": "念力控制的都市英雄", "type": "核心主題"},
            {"keyword": "變身術的間諜任務", "type": "核心主題"},
            {"keyword": "治癒能力的醫療奇蹟", "type": "核心主題"},
            {"keyword": "元素操縱的自然災難", "type": "核心主題"},
            {"keyword": "記憶刪除的秘密組織", "type": "核心主題"},
            {"keyword": "超速奔跑的競技挑戰", "type": "核心主題"},
            {"keyword": "幻覺製造的心理戰", "type": "核心主題"},
            {"keyword": "不死之身的極限測試", "type": "核心主題"},
            {"keyword": "空間折疊的旅行捷徑", "type": "核心主題"},
            {"keyword": "電磁操控的科技黑客", "type": "核心主題"},
            {"keyword": "重力逆轉的建築危機", "type": "核心主題"},
            {"keyword": "靈魂交換的身份混亂", "type": "核心主題"},
            {"keyword": "火焰噴射的火災救援", "type": "核心主題"},
            {"keyword": "冰凍能力的寒冬戰鬥", "type": "核心主題"},
            {"keyword": "植物生長的綠色革命", "type": "核心主題"},
            # 輔助元素
            {"keyword": "超能力覺醒的儀式", "type": "輔助元素"},
            {"keyword": "讀心耳機的偽裝", "type": "輔助元素"},
            {"keyword": "時間手錶的調節", "type": "輔助元素"},
            {"keyword": "隱形斗篷的穿戴", "type": "輔助元素"},
            {"keyword": "預知水晶的凝視", "type": "輔助元素"},
            {"keyword": "動物項圈的通訊", "type": "輔助元素"},
            {"keyword": "移動門戶的開啟", "type": "輔助元素"},
            {"keyword": "念力手鐲的激活", "type": "輔助元素"},
            {"keyword": "變身藥劑的服用", "type": "輔助元素"},
            {"keyword": "治癒手套的觸摸", "type": "輔助元素"},
            {"keyword": "元素戒指的召喚", "type": "輔助元素"},
            {"keyword": "記憶擦除的裝置", "type": "輔助元素"},
            {"keyword": "奔跑鞋子的加速", "type": "輔助元素"},
            {"keyword": "幻覺面具的戴上", "type": "輔助元素"},
            {"keyword": "不死護符的保護", "type": "輔助元素"},
            {"keyword": "空間背包的儲存", "type": "輔助元素"},
            {"keyword": "電磁手環的操控", "type": "輔助元素"},
            {"keyword": "重力靴子的反轉", "type": "輔助元素"},
            {"keyword": "交換項鍊的連結", "type": "輔助元素"},
            {"keyword": "火焰手套的點燃", "type": "輔助元素"},
            {"keyword": "冰凍護腕的凍結", "type": "輔助元素"},
            {"keyword": "植物種子的播撒", "type": "輔助元素"}
        ],
        "末日求生": [
            # 核心主題
            {"keyword": "病毒爆發的避難所建設", "type": "核心主題"},
            {"keyword": "核戰後的廢土探索", "type": "核心主題"},
            {"keyword": "外星入侵的抵抗戰鬥", "type": "核心主題"},
            {"keyword": "氣候變遷的生存適應", "type": "核心主題"},
            {"keyword": "喪屍圍城的突圍行動", "type": "核心主題"},
            {"keyword": "資源短缺的部落衝突", "type": "核心主題"},
            {"keyword": "地下掩體的長期生活", "type": "核心主題"},
            {"keyword": "變異動物的狩獵挑戰", "type": "核心主題"},
            {"keyword": "末日車隊的遷徙旅程", "type": "核心主題"},
            {"keyword": "科技遺跡的發掘利用", "type": "核心主題"},
            {"keyword": "人類進化的基因變異", "type": "核心主題"},
            {"keyword": "海洋淹沒的浮島求生", "type": "核心主題"},
            {"keyword": "黑暗降臨的永夜生存", "type": "核心主題"},
            {"keyword": "機器叛變的電子戰", "type": "核心主題"},
            {"keyword": "食物鏈崩潰的覓食危機", "type": "核心主題"},
            {"keyword": "輻射區的防護探險", "type": "核心主題"},
            {"keyword": "末日商人的交易網絡", "type": "核心主題"},
            {"keyword": "心理崩潰的團隊分裂", "type": "核心主題"},
            {"keyword": "重啟文明的種子計劃", "type": "核心主題"},
            {"keyword": "時間悖論的輪迴末日", "type": "核心主題"},
            {"keyword": "超自然力量的靈異末世", "type": "核心主題"},
            {"keyword": "太空殖民的地球回歸", "type": "核心主題"},
            # 輔助元素
            {"keyword": "避難所門的強化", "type": "輔助元素"},
            {"keyword": "廢土地圖的繪製", "type": "輔助元素"},
            {"keyword": "抵抗武器的製作", "type": "輔助元素"},
            {"keyword": "氣候防護的裝備", "type": "輔助元素"},
            {"keyword": "喪屍陷阱的設置", "type": "輔助元素"},
            {"keyword": "部落營火的聚會", "type": "輔助元素"},
            {"keyword": "掩體通風的系統", "type": "輔助元素"},
            {"keyword": "狩獵弓箭的瞄準", "type": "輔助元素"},
            {"keyword": "車隊燃料的補給", "type": "輔助元素"},
            {"keyword": "遺跡密碼的破解", "type": "輔助元素"},
            {"keyword": "基因血清的注射", "type": "輔助元素"},
            {"keyword": "浮島繩索的連結", "type": "輔助元素"},
            {"keyword": "永夜燈光的點亮", "type": "輔助元素"},
            {"keyword": "機器防火牆的構築", "type": "輔助元素"},
            {"keyword": "覓食背包的裝填", "type": "輔助元素"},
            {"keyword": "輻射服的穿戴", "type": "輔助元素"},
            {"keyword": "交易貨物的交換", "type": "輔助元素"},
            {"keyword": "團隊會議的爭執", "type": "輔助元素"},
            {"keyword": "種子庫的開啟", "type": "輔助元素"},
            {"keyword": "輪迴日記的記錄", "type": "輔助元素"},
            {"keyword": "靈異護符的佩戴", "type": "輔助元素"},
            {"keyword": "太空艙的著陸", "type": "輔助元素"}
        ],
        "都市修仙": [
            # 核心主題
            {"keyword": "隱世高人的都市歸來", "type": "核心主題"},
            {"keyword": "靈氣復甦的修煉狂潮", "type": "核心主題"},
            {"keyword": "古武家族的現代衝突", "type": "核心主題"},
            {"keyword": "丹藥煉製的商業帝國", "type": "核心主題"},
            {"keyword": "法寶拍賣的地下市場", "type": "核心主題"},
            {"keyword": "都市妖獸的獵殺行動", "type": "核心主題"},
            {"keyword": "仙門弟子的校園生活", "type": "核心主題"},
            {"keyword": "渡劫雷霆的都市天劫", "type": "核心主題"},
            {"keyword": "靈脈爭奪的權力博弈", "type": "核心主題"},
            {"keyword": "修仙APP的科技融合", "type": "核心主題"},
            {"keyword": "隱藏宗門的曝光危機", "type": "核心主題"},
            {"keyword": "仙界通道的開啟冒險", "type": "核心主題"},
            {"keyword": "都市鬼修的陰魂對抗", "type": "核心主題"},
            {"keyword": "靈丹妙藥的醫療革命", "type": "核心主題"},
            {"keyword": "飛劍縱橫的交通混亂", "type": "核心主題"},
            {"keyword": "修仙直播的網紅現象", "type": "核心主題"},
            {"keyword": "古仙遺跡的都市發掘", "type": "核心主題"},
            {"keyword": "雙修伴侶的感情糾葛", "type": "核心主題"},
            {"keyword": "天道規則的現代違背", "type": "核心主題"},
            {"keyword": "仙帝轉世的低調崛起", "type": "核心主題"},
            {"keyword": "靈獸契約的寵物潮流", "type": "核心主題"},
            {"keyword": "修仙大學的招生考試", "type": "核心主題"},
            # 輔助元素
            {"keyword": "靈石交易的銀行", "type": "輔助元素"},
            {"keyword": "修煉丹爐的煉製", "type": "輔助元素"},
            {"keyword": "家族徽章的傳承", "type": "輔助元素"},
            {"keyword": "拍賣錘子的敲擊", "type": "輔助元素"},
            {"keyword": "妖獸陷阱的布置", "type": "輔助元素"},
            {"keyword": "校園陣法的佈置", "type": "輔助元素"},
            {"keyword": "雷劫雲層的聚集", "type": "輔助元素"},
            {"keyword": "靈脈探測的儀器", "type": "輔助元素"},
            {"keyword": "APP升級的系統", "type": "輔助元素"},
            {"keyword": "宗門令牌的驗證", "type": "輔助元素"},
            {"keyword": "通道符文的激活", "type": "輔助元素"},
            {"keyword": "鬼修法器的祭煉", "type": "輔助元素"},
            {"keyword": "妙藥配方的研發", "type": "輔助元素"},
            {"keyword": "飛劍遙控的駕駛", "type": "輔助元素"},
            {"keyword": "直播鏡頭的切換", "type": "輔助元素"},
            {"keyword": "遺跡地圖的解讀", "type": "輔助元素"},
            {"keyword": "雙修功法的修煉", "type": "輔助元素"},
            {"keyword": "天道誓言的立下", "type": "輔助元素"},
            {"keyword": "轉世記憶的覺醒", "type": "輔助元素"},
            {"keyword": "靈獸蛋的孵化", "type": "輔助元素"},
            {"keyword": "考試卷子的作答", "type": "輔助元素"},
            {"keyword": "仙氣測試的儀表", "type": "輔助元素"}
        ],
        "霸道總裁": [
            # 核心主題
            {"keyword": "契約婚姻的甜蜜轉折", "type": "核心主題"},
            {"keyword": "職場灰姑娘的逆襲愛情", "type": "核心主題"},
            {"keyword": "復仇總裁的溫柔陷阱", "type": "核心主題"},
            {"keyword": "豪門繼承的權力遊戲", "type": "核心主題"},
            {"keyword": "明星緋聞的真愛曝光", "type": "核心主題"},
            {"keyword": "保鏢保護的禁忌戀情", "type": "核心主題"},
            {"keyword": "商業聯姻的真情告白", "type": "核心主題"},
            {"keyword": "失憶總裁的記憶追尋", "type": "核心主題"},
            {"keyword": "設計師與老闆的靈感碰撞", "type": "核心主題"},
            {"keyword": "醫生救治的醫患緣分", "type": "核心主題"},
            {"keyword": "旅行邂逅的浪漫假期", "type": "核心主題"},
            {"keyword": "網紅直播的幕後操控", "type": "核心主題"},
            {"keyword": "家庭恩怨的化解愛戀", "type": "核心主題"},
            {"keyword": "廚師比賽的味覺誘惑", "type": "核心主題"},
            {"keyword": "律師辯護的法庭外情", "type": "核心主題"},
            {"keyword": "藝術家與贊助人的創作火花", "type": "核心主題"},
            {"keyword": "運動員教練的激勵愛情", "type": "核心主題"},
            {"keyword": "科學家助手的實驗戀曲", "type": "核心主題"},
            {"keyword": "書店遇見的文學緣分", "type": "核心主題"},
            {"keyword": "咖啡廳的日常邂逅", "type": "核心主題"},
            {"keyword": "電影拍攝的戲裡戲外", "type": "核心主題"},
            {"keyword": "音樂會上的旋律共鳴", "type": "核心主題"},
            # 輔助元素
            {"keyword": "豪華跑車的兜風", "type": "輔助元素"},
            {"keyword": "私人飛機的旅行", "type": "輔助元素"},
            {"keyword": "鑽石項鍊的禮物", "type": "輔助元素"},
            {"keyword": "西裝革履的帥氣", "type": "輔助元素"},
            {"keyword": "會議室的爭執", "type": "輔助元素"},
            {"keyword": "晚宴舞會的邀請", "type": "輔助元素"},
            {"keyword": "海邊別墅的度假", "type": "輔助元素"},
            {"keyword": "記憶相冊的翻閱", "type": "輔助元素"},
            {"keyword": "設計稿件的修改", "type": "輔助元素"},
            {"keyword": "手術室的緊張", "type": "輔助元素"},
            {"keyword": "景點拍照的回憶", "type": "輔助元素"},
            {"keyword": "直播鏡頭的切換", "type": "輔助元素"},
            {"keyword": "家庭飯局的尷尬", "type": "輔助元素"},
            {"keyword": "廚房烹飪的互動", "type": "輔助元素"},
            {"keyword": "法庭陳詞的辯論", "type": "輔助元素"},
            {"keyword": "畫廊展覽的欣賞", "type": "輔助元素"},
            {"keyword": "訓練場的汗水", "type": "輔助元素"},
            {"keyword": "實驗室的意外", "type": "輔助元素"},
            {"keyword": "書架選書的討論", "type": "輔助元素"},
            {"keyword": "咖啡香氣的瀰漫", "type": "輔助元素"},
            {"keyword": "片場休息的聊天", "type": "輔助元素"},
            {"keyword": "音樂旋律的哼唱", "type": "輔助元素"}
        ],
        "青春": [
            # 核心主題
            {"keyword": "校園戀愛的青澀回憶", "type": "核心主題"},
            {"keyword": "籃球社的團隊友情", "type": "核心主題"},
            {"keyword": "畢業旅行的冒險故事", "type": "核心主題"},
            {"keyword": "音樂社團的夢想追逐", "type": "核心主題"},
            {"keyword": "叛逆少年的成長蛻變", "type": "核心主題"},
            {"keyword": "暗戀告白的勇氣時刻", "type": "核心主題"},
            {"keyword": "家庭衝突的和解過程", "type": "核心主題"},
            {"keyword": "社團活動的熱血比賽", "type": "核心主題"},
            {"keyword": "暑假打工的意外邂逅", "type": "核心主題"},
            {"keyword": "校園霸凌的正義對抗", "type": "核心主題"},
            {"keyword": "藝術展覽的創作靈感", "type": "核心主題"},
            {"keyword": "交換日記的秘密分享", "type": "核心主題"},
            {"keyword": "運動會的拼搏精神", "type": "核心主題"},
            {"keyword": "網友見面的友情建立", "type": "核心主題"},
            {"keyword": "考試壓力的共同奮鬥", "type": "核心主題"},
            {"keyword": "旅行社的探險經歷", "type": "核心主題"},
            {"keyword": "舞蹈表演的舞台光芒", "type": "核心主題"},
            {"keyword": "文學社的寫作激情", "type": "核心主題"},
            {"keyword": "寵物陪伴的溫暖故事", "type": "核心主題"},
            {"keyword": "節日慶祝的歡樂時光", "type": "核心主題"},
            {"keyword": "轉校生的適應挑戰", "type": "核心主題"},
            {"keyword": "青春日記的記錄點滴", "type": "核心主題"},
            # 輔助元素
            {"keyword": "課桌便條的傳遞", "type": "輔助元素"},
            {"keyword": "籃球場的投籃", "type": "輔助元素"},
            {"keyword": "火車窗外的風景", "type": "輔助元素"},
            {"keyword": "吉他彈奏的旋律", "type": "輔助元素"},
            {"keyword": "家長會議的爭論", "type": "輔助元素"},
            {"keyword": "告白信件的投遞", "type": "輔助元素"},
            {"keyword": "家庭晚餐的對話", "type": "輔助元素"},
            {"keyword": "比賽哨聲的響起", "type": "輔助元素"},
            {"keyword": "打工制服的穿戴", "type": "輔助元素"},
            {"keyword": "霸凌事件的目擊", "type": "輔助元素"},
            {"keyword": "畫布顏料的塗抹", "type": "輔助元素"},
            {"keyword": "日記本的書寫", "type": "輔助元素"},
            {"keyword": "接力棒的傳遞", "type": "輔助元素"},
            {"keyword": "網路訊息的回覆", "type": "輔助元素"},
            {"keyword": "考卷發下的緊張", "type": "輔助元素"},
            {"keyword": "探險背包的裝填", "type": "輔助元素"},
            {"keyword": "舞蹈鞋的綁帶", "type": "輔助元素"},
            {"keyword": "筆記本的翻頁", "type": "輔助元素"},
            {"keyword": "寵物項圈的戴上", "type": "輔助元素"},
            {"keyword": "節日燈光的點亮", "type": "輔助元素"},
            {"keyword": "新同學的介紹", "type": "輔助元素"},
            {"keyword": "日記封面的裝飾", "type": "輔助元素"}
        ],
        "輕小說": [
            # 核心主題
            {"keyword": "異世界召喚的勇者之旅", "type": "核心主題"},
            {"keyword": "校園魔法的日常趣事", "type": "核心主題"},
            {"keyword": "機械少女的感情覺醒", "type": "核心主題"},
            {"keyword": "冒險公會的任務生活", "type": "核心主題"},
            {"keyword": "時間旅行者的歷史干預", "type": "核心主題"},
            {"keyword": "虛擬遊戲的現實交織", "type": "核心主題"},
            {"keyword": "精靈契約的友情羈絆", "type": "核心主題"},
            {"keyword": "偵探社團的謎團解謎", "type": "核心主題"},
            {"keyword": "料理大賽的美食挑戰", "type": "核心主題"},
            {"keyword": "音樂精靈的旋律冒險", "type": "核心主題"},
            {"keyword": "寵物變人的搞笑日常", "type": "核心主題"},
            {"keyword": "隱藏能力的校園英雄", "type": "核心主題"},
            {"keyword": "古代遺跡的寶藏探索", "type": "核心主題"},
            {"keyword": "魔法書店的奇幻故事", "type": "核心主題"},
            {"keyword": "機器人學校的學生生活", "type": "核心主題"},
            {"keyword": "龍與騎士的和平協定", "type": "核心主題"},
            {"keyword": "夢境世界的現實連結", "type": "核心主題"},
            {"keyword": "超能力者的都市隱居", "type": "核心主題"},
            {"keyword": "動物王國的王位繼承", "type": "核心主題"},
            {"keyword": "星際旅行的太空奇遇", "type": "核心主題"},
            {"keyword": "仙女下凡的凡間體驗", "type": "核心主題"},
            {"keyword": "漫畫社的創作激情", "type": "核心主題"},
            # 輔助元素
            {"keyword": "召喚法陣的發光", "type": "輔助元素"},
            {"keyword": "魔法課本的翻閱", "type": "輔助元素"},
            {"keyword": "機械關節的轉動", "type": "輔助元素"},
            {"keyword": "任務告示的張貼", "type": "輔助元素"},
            {"keyword": "時間機器的啟動", "type": "輔助元素"},
            {"keyword": "遊戲頭盔的戴上", "type": "輔助元素"},
            {"keyword": "契約寶石的閃耀", "type": "輔助元素"},
            {"keyword": "謎團線索的收集", "type": "輔助元素"},
            {"keyword": "料理食材的準備", "type": "輔助元素"},
            {"keyword": "音樂盒子的旋律", "type": "輔助元素"},
            {"keyword": "寵物尾巴的搖擺", "type": "輔助元素"},
            {"keyword": "能力徽章的佩戴", "type": "輔助元素"},
            {"keyword": "遺跡門口的開啟", "type": "輔助元素"},
            {"keyword": "書架魔法的觸發", "type": "輔助元素"},
            {"keyword": "學生證的刷卡", "type": "輔助元素"},
            {"keyword": "和平條約的簽署", "type": "輔助元素"},
            {"keyword": "夢境門戶的穿越", "type": "輔助元素"},
            {"keyword": "能力抑制器的移除", "type": "輔助元素"},
            {"keyword": "王冠寶石的鑲嵌", "type": "輔助元素"},
            {"keyword": "太空艙的浮遊", "type": "輔助元素"},
            {"keyword": "仙女翅膀的扇動", "type": "輔助元素"},
            {"keyword": "漫畫筆的繪製", "type": "輔助元素"}
        ],
        "default": [
            # 核心主題
            {"keyword": "神秘系統的綁定冒險", "type": "核心主題"},
            {"keyword": "穿越重生的命運逆轉", "type": "核心主題"},
            {"keyword": "金手指覺醒的無敵之路", "type": "核心主題"},
            {"keyword": "宗門爭霸的權力鬥爭", "type": "核心主題"},
            {"keyword": "寶物爭奪的激烈競賽", "type": "核心主題"},
            {"keyword": "修煉突破的境界飛躍", "type": "核心主題"},
            {"keyword": "復仇之路的血腥復仇", "type": "核心主題"},
            {"keyword": "紅顏知己的感情糾葛", "type": "核心主題"},
            {"keyword": "試煉秘境的生死考驗", "type": "核心主題"},
            {"keyword": "天驕對決的巔峰戰鬥", "type": "核心主題"},
            {"keyword": "家族傳承的血脈覺醒", "type": "核心主題"},
            {"keyword": "仙界登臨的飛升之旅", "type": "核心主題"},
            {"keyword": "魔道崛起的黑暗統治", "type": "核心主題"},
            {"keyword": "紅顏知己的感情糾葛", "type": "核心主題"},
            {"keyword": "靈寵契約的忠誠夥伴", "type": "核心主題"},
            {"keyword": "丹道大師的煉藥奇蹟", "type": "核心主題"},
            {"keyword": "陣法佈置的防禦奇陣", "type": "核心主題"},
            {"keyword": "劍道極致的劍意領悟", "type": "核心主題"},
            {"keyword": "體修霸道的肉身成聖", "type": "核心主題"},
            {"keyword": "魂修幽冥的靈魂操控", "type": "核心主題"},
            {"keyword": "神通廣大的法術對轟", "type": "核心主題"},
            {"keyword": "禁地探險的機緣奪取", "type": "核心主題"},
            {"keyword": "天劫渡過的雷霆洗禮", "type": "核心主題"},
            # 輔助元素
            {"keyword": "系統面板的查看", "type": "輔助元素"},
            {"keyword": "重生記憶的融合", "type": "輔助元素"},
            {"keyword": "金手指道具的使用", "type": "輔助元素"},
            {"keyword": "宗門令牌的驗證", "type": "輔助元素"},
            {"keyword": "寶物光輝的綻放", "type": "輔助元素"},
            {"keyword": "修為丹田的運轉", "type": "輔助元素"},
            {"keyword": "仇敵名單的劃除", "type": "輔助元素"},
            {"keyword": "知己項鍊的佩戴", "type": "輔助元素"},
            {"keyword": "秘境地圖的導航", "type": "輔助元素"},
            {"keyword": "對決擂台的登上", "type": "輔助元素"},
            {"keyword": "血脈測試的儀式", "type": "輔助元素"},
            {"keyword": "飛升通道的開啟", "type": "輔助元素"},
            {"keyword": "魔道祭壇的獻祭", "type": "輔助元素"},
            {"keyword": "靈寵蛋的孵化", "type": "輔助元素"},
            {"keyword": "煉丹爐火的點燃", "type": "輔助元素"},
            {"keyword": "陣旗插立的佈局", "type": "輔助元素"},
            {"keyword": "劍芒斬擊的揮舞", "type": "輔助元素"},
            {"keyword": "肉身鍛鍊的淬煉", "type": "輔助元素"},
            {"keyword": "魂魄出竅的遊離", "type": "輔助元素"},
            {"keyword": "法術符文的描繪", "type": "輔助元素"},
            {"keyword": "禁地結界的破解", "type": "輔助元素"},
            {"keyword": "雷劫護符的抵擋", "type": "輔助元素"}
        ]
    }

    # 角色名稱資源庫
    MALE_NAMES = [ 
        "李強", "張偉", "王磊", "陳浩", "楊明", "劉峰", "趙剛", "孫宇",
        "周傑", "吳剛", "鄭雄", "林浩然", "徐峰", "馬超", "唐龍", "黃毅",
        "崔浩", "謝霆", "羅宇", "高翔",
        "王偉", "李偉", "劉偉", "張敏", "李靜", "王靜", "王芳", "李娜",
        "浩然", "子軒", "皓軒", "宇軒", "浩宇", "亦辰", "宇辰", "子墨",
        "宇航", "梓豪", "亦宸", "俊熙", "澤楷", "博文", "俊傑", "明軒",
        "立誠", "志遠", "文昊", "天佑", "英傑", "哲瀚", "雨澤", "國棟",
        "建國", "建華", "國華", "和平", "建平", "軍", "斌", "勇",
        "家豪", "志明", "建宏", "俊宏", "志豪", "志偉", "文雄", "承翰",
        "冠宇", "彥霖", "凱文", "嘉誠", "政諺", "宥翔", "承恩", "柏翰",
        "睿恩", "品睿", "宸睿", "柏諺", "宥廷", "祐愷", "子謙", "彥廷",
        "冠廷", "紹安", "宗翰", "宇傑", "紹齊", "致遠", "博宇", "承澤",
        "德佑", "翰林", "景曦", "嘉熙", "敬軒", "楷瑞", "力言", "明傑",
        "啟航", "擎宇", "瑞霖", "紹輝", "聖傑", "思源", "天翊", "偉宸",
        "文博", "曦晨", "曜坤", "熠彤", "永昌", "展鵬", "正豪", "志新",
        "子涵", "弘文", "峻熙", "嘉懿", "鴻濤", "偉祺", "越彬", "風華",
        "靖琪", "明輝", "旺霖", "鑫磊", "燁磊", "昊然", "子豪", "辰逸"
    ]

    FEMALE_NAMES = [
        "林曉晴", "張曉雯", "王若雪", "李靜怡", "陳美琪", "楊婉婷", "劉雨婷",
        "趙雅琳", "孫曉雯", "周曼麗", "吳瑤", "鄭曉雯", "林芷晴", "徐曼妮",
        "馬曉涵", "唐曉萱", "黃曉雯", "崔麗娜", "謝若蘭", "羅曉晴",
        "秀英", "桂英", "秀蘭", "玉蘭", "桂蘭", "秀珍", "鳳英", "玉珍",
        "玉英", "蘭英", "萍", "紅", "麗", "敏", "靜", "芳",
        "梓萱", "梓涵", "詩涵", "一諾", "依諾", "欣怡", "語桐", "欣妍",
        "可欣", "語汐", "雨桐", "夢瑤", "晨曦", "若曦", "思穎", "雪芬",
        "曉慧", "麗娟", "雅靜", "韻寒", "莉姿", "沛玲", "歆瑤", "凌菲",
        "夢潔", "惠芳", "淑芬", "淑惠", "美玲", "雅玲", "麗華", "春嬌",
        "語彤", "品妍", "詠晴", "子晴", "品萱", "子涵", "采潔", "宥蓁",
        "思妤", "芯恬", "宜蓁", "詩涵", "庭妤", "羽喬", "姿吟", "恩恩",
        "安琪", "蓓蕾", "碧瑶", "燦琳", "丹妮", "恩熙", "芳華", "格菲",
        "海倫", "惠茜", "佳寧", "瑾萱", "晶晶", "珂玥", "蘭馨", "樂怡",
        "琳琅", "夢琪", "敏萱", "娜蘭", "寧馨", "佩珊", "琪華", "倩雪",
        "晴川", "蓉蓉", "蕊姬", "思涵", "恬靜", "婉儀", "薇薇", "熙媛",
        "夏嵐", "馨悅", "雅芙", "嫣然", "伊人", "穎慧", "語嫣", "芸熙",
        "芷若", "子怡", "曉萱", "雪雁", "月嬋", "雲舒", "韶涵", "靜璇"
    ]


    titles_file = TITLES_FILE_PATH
    os.makedirs(os.path.dirname(titles_file), exist_ok=True)
    existing_titles = set()
    if os.path.exists(titles_file):
        with open(titles_file, "r", encoding="utf-8") as f:
            existing_titles = set(line.strip() for line in f if line.strip())

    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        
        main_genre = random.choice(MAIN_GENRES)
        keywords_pool = GENRE_SPECIFIC_KEYWORDS.get(main_genre, GENRE_SPECIFIC_KEYWORDS["default"])
        
        core_keywords = [kw for kw in keywords_pool if kw["type"] == "核心主題"]
        sub_keywords = [kw for kw in keywords_pool if kw["type"] == "輔助元素"]
        
        if not core_keywords:
            print(f"警告：類別 '{main_genre}' 沒有核心主題，跳過。")
            continue

        core_keyword = random.choice(core_keywords)
        creative_sparks_obj = [core_keyword]
        
        if sub_keywords:
            num_sub_keywords = random.randint(1, 4)
            num_to_sample = min(num_sub_keywords, len(sub_keywords))
            selected_subs = random.sample(sub_keywords, num_to_sample)
            creative_sparks_obj.extend(selected_subs)
        
        creative_sparks_str = ", ".join([kw["keyword"] for kw in creative_sparks_obj])
        global_seed = random.randint(1, 100000)

        # 隨機決定主角性別 (50% 機率)
        main_character_gender = "女性" if random.random() < 0.3 else "男性"

        # 在while循環內，隨機選主角候選（根據性別）
        candidate_main_names = random.sample(MALE_NAMES if main_character_gender == '男性' else FEMALE_NAMES, 8)
        main_names_str = ', '.join(candidate_main_names)

        # 配角候選（混合男女）
        all_names = MALE_NAMES + FEMALE_NAMES
        candidate_supporting_names = random.sample(all_names, 8)
        supporting_names_str = ', '.join(candidate_supporting_names)        

        system_prompt = f"""
        你是一位擅長創作的網文作家，專注打造讓年輕讀者無腦享受的小說。你的任務是根據指定的主類型和核心創意關鍵詞，構思一個小說大綱，並以 JSON 格式輸出。請嚴格遵循以下規則和格式：
        - **NOVEL_NAME**：用20~25字概述劇情核心，生動描述，盡量不要寫的像書名一樣，而是像是用20~25字讓人知道這本小說是甚麼。
        - **NOVEL_GENRE**：逗號分隔的字串，第一個類型為指定主類型，後面添加1~3個簡單副類型。
        - **TARGET_TOTAL_WORDS**：選擇12000~20000中文字數，根據劇情需求。
        - **MAIN_CHARACTER_GENDER**：主角性別為 {main_character_gender}。
        - **MAIN_CHARACTERS**：對象列表，每個對象包含 role、name 和 description。包括 1~2 名主角，姓名從以下 8 個隨機選取的名字中選擇：{main_names_str}。
        - **SUPPORTING_CHARACTERS**：對象列表，每個對象包含 role、name 和 description。包括 1~3 名配角，姓名從以下 8 個隨機選取的名字中選擇：{supporting_names_str}。
        - **WORLDVIEW_SETTING**：單一文本，2~3行，詳細描述故事世界背景。
        - **MAIN_PLOT**：單一文本，3~5行，完整描述故事主線，。
        - **NOVEL_INTRO**：單一文本，100~150字，簡要介紹背景和主角境遇，營造懸念，吸引讀者，切勿劇透核心劇情。
        """

        user_messages = f"""
        【創作指令】
        - 主類型：{main_genre}
        - 核心創意關鍵詞：{creative_sparks_str}

        【最終指令】
        僅返回一個完整的user_prompt_config JSON對象，不要包含任何額外說明或markdown標記。
        """
        params = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_messages}
            ],
            "max_tokens": 16384,
            "temperature": random.uniform(0.7, 0.9),
            "top_p": random.uniform(0.85, 0.95),
            "n": 1,
            "seed": global_seed
        }

        try:
            completion = client.chat.completions.create(**params)
            raw_content = completion.choices[0].message.content.strip()
            
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_content)
            content = json_match.group(1) if json_match else raw_content
            
            user_prompt_config = json.loads(content)

            if "user_prompt_config" in user_prompt_config and isinstance(user_prompt_config["user_prompt_config"], dict):
                user_prompt_config = user_prompt_config["user_prompt_config"]
            
            required_fields = ["NOVEL_NAME", "NOVEL_GENRE", "TARGET_TOTAL_WORDS", "MAIN_CHARACTERS", "MAIN_CHARACTER_GENDER", "SUPPORTING_CHARACTERS", "WORLDVIEW_SETTING", "MAIN_PLOT", "NOVEL_INTRO"]
            if not all(field in user_prompt_config for field in required_fields):
                raise ValueError(f"生成的JSON字段缺失: {list(user_prompt_config.keys())}")

            # 確保主角性別符合預設
            user_prompt_config["MAIN_CHARACTER_GENDER"] = main_character_gender

            final_title = user_prompt_config["NOVEL_NAME"]
            if final_title not in existing_titles:
                with open(titles_file, "a", encoding="utf-8") as f:
                    f.write(final_title + "\n")
                
                novel_dir = os.path.join(output_dir, final_title)
                config_dir = os.path.join(novel_dir, "user_prompt_config")
                os.makedirs(config_dir, exist_ok=True)
                config_path = os.path.join(config_dir, f"{final_title}_config.json")
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(user_prompt_config, f, ensure_ascii=False, indent=4)
                
                print(f"成功生成故事概述: {final_title}")
                print(f"配置文件已保存至: {config_path}")
                return user_prompt_config, config_path, global_seed

            print(f"標題 '{final_title}' 已存在，重新生成 (嘗試 {attempt}/{max_attempts})...")

        except Exception as e:
            print(f"生成或解析 JSON 失敗 (嘗試 {attempt}/{max_attempts}): {e}")
            print(f"創意關鍵詞: {creative_sparks_str}")
            print(f"原始內容:\n{raw_content}\n---")
    print("超過最大嘗試次數，無法生成不重複標題")
    return None, None, None

# ==============================================================================
# --- 生成劇本大綱 ---
# ==============================================================================

def generate_task_descriptions(user_prompt, client):
    """
    生成十二章節結構的劇情目標，確保劇情連貫且爽點突出。
    """
    print("正在生成動態劇本大綱...")

    main_characters_list = [
        f"姓名：{char.get('name', '未知')}\n角色定位：{char.get('role', '未設定')}\n詳細描述：{char.get('description', '無')}"
        for char in user_prompt['MAIN_CHARACTERS']
    ]
    main_characters_str = '\n'.join(main_characters_list)

    supporting_characters_list = [
        f"姓名：{char.get('name', '未知')}\n角色定位：{char.get('role', '未設定')}\n詳細描述：{char.get('description', '無')}"
        for char in user_prompt.get('SUPPORTING_CHARACTERS', [])
    ]
    supporting_characters_str = '\n'.join(supporting_characters_list)

    system_prompt = """
你是一位頂級網文大神，擅長把控劇情節奏。你的任務是根據【小說核心設定】生成一個十二章節結構劇本大綱。請嚴格遵循以下規則，基於【小說核心設定】主動規劃大綱，確保與"類型"和"主線劇情"一致，並適應小說類型。

1. **任務描述原則**：
   - 每個任務描述詳細（100~200字），聚焦該章節核心劇情目標。
   - 第一章節需快速吸引讀者對後續劇情發展的渴望。
   - 最終章節需完整結束故事，無懸念，給讀者滿足感，強調主角最終成長與圓滿結局。

2. **類型適應與成長設計**：
   - 主動基於NOVEL_GENRE，選擇合適的成長形式，避免跨類型混亂。
   - 整合主要角色和配角，突出他們在該章的互動或貢獻。
   - 強調成長自然融入劇情，避免突兀。

3. **大綱連貫性**：
   - 確保整體劇情連貫。
   - 避免引入未在核心設定中的元素；如果擴展，必須邏輯符合世界觀。
   - 避免重複套路，增加原創轉折。
"""
    user_messages = f"""
【小說核心設定】
- 小說名稱：{user_prompt['NOVEL_NAME']}
- 類型：{user_prompt['NOVEL_GENRE']}
- 世界觀設定：{user_prompt['WORLDVIEW_SETTING']}
- 主線劇情：{user_prompt['MAIN_PLOT']}
- 主要角色：
{main_characters_str}
- 配角：
{supporting_characters_str}

【你的任務】
生成一個十二章節結構的劇情目標（任務描述），返回JSON對象，格式如下：
{{
  "第一章節": "描述第一章節（進度約8.33%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第二章節": "描述第二章節（進度約16.67%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第三章節": "描述第三章節（進度約25%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第四章節": "描述第四章節（進度約33.33%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第五章節": "描述第五章節（進度約41.67%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第六章節": "描述第六章節（進度約50%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第七章節": "描述第七章節（進度約58.33%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第八章節": "描述第八章節（進度約66.67%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第九章節": "描述第九章節（進度約75%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第十章節": "描述第十章節（進度約83.33%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "第十一章節": "描述第十一章節（進度約91.67%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動）",
  "最終章節": "描述最終章節（進度約100%，約{user_prompt['TARGET_TOTAL_WORDS']//12}字，允許上下浮動，完整結束故事，無懸念）"
}}

【最終指令】
僅返回JSON對象，包含十二個章節的任務描述，不要包含任何額外說明或markdown標記。
"""
    try:
        params = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_messages}
            ],
            "max_tokens": 16384,
            "temperature": random.uniform(0.7, 0.8),
            "top_p": random.uniform(0.9, 0.95),
            "response_format": {"type": "json_object"}
        }
        completion = client.chat.completions.create(**params)
        task_descriptions = json.loads(completion.choices[0].message.content)
        print(f"成功生成動態劇本大綱：\n{json.dumps(task_descriptions, ensure_ascii=False, indent=2)}")
        return task_descriptions
    except Exception as e:
        print(f"!!!!!!!! [錯誤] 生成動態劇本大綱失敗: {e} !!!!!!!!")
        return None

# ==============================================================================
# --- 更新故事狀態的AI角色 ---
# ==============================================================================
def update_story_state(client, previous_state, new_chapter_content, user_prompt):
    """
    使用AI更新故事狀態，記錄角色能力、感情、關係等，並刪除舊的或不再出現的角色。
    """
    system_prompt = """
你是一位故事狀態管理者，負責基於先前狀態和新章節內容，更新角色狀態。狀態包括每個角色的能力、感情狀態、關係等。刪除過時的或不再出現的角色（如果該角色在新章節中未提及，且在先前狀態中已無關鍵作用）。輸出僅為更新後的JSON對象，結構如下：
{
  "characters": {
    "角色姓名1": {
      "abilities": ["能力1", "能力2"],
      "emotions": "當前感情描述",
      "relationships": {"角色姓名2": "關係描述", "角色姓名3": "關係描述"}
    },
    "角色姓名2": {...}
  }
}
確保狀態簡潔、相關。
"""
    user_messages = f"""
【先前狀態】
{previous_state if previous_state else '無（這是初始狀態，從核心設定初始化）'}

【新章節內容】
{new_chapter_content}

【最終指令】
僅返回更新後的JSON狀態對象，不要包含任何額外說明。
"""
    try:
        params = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_messages}
            ],
            "max_tokens": 30000,
            "temperature": 0.7,
            "top_p": 0.9,
            "response_format": {"type": "json_object"}
        }
        completion = client.chat.completions.create(**params)
        updated_state = completion.choices[0].message.content
        return updated_state
    except Exception as e:
        print(f"更新故事狀態失敗: {e}")
        return previous_state  # 如果失敗，返回先前狀態
# ==============================================================================
# --- 生成小說 ---
# ==============================================================================
def generate_novel(user_prompt, output_dir=BASE_OUTPUT_DIR):
    """
    生成高品質短篇爽感小說，分12章節生成，總字數約12000~20000字，確保劇情連貫。
    """
    global_seed = random.randint(1, 100000)
    print(f"本次小說生成任務使用的全局種子是: {global_seed}")
    # --- 環境與客戶端初始化 ---
    current_file_path = os.path.abspath(__file__)
    current_folder_path = os.path.dirname(current_file_path)
    env_path = os.path.join(current_folder_path, 'XAI_API_KEY.env')
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("XAI_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    translator_en_to_zh = GoogleTranslator(source='en', target='zh-TW')
    # --- 驗證與參數設定 ---
    required_fields = ["NOVEL_NAME", "NOVEL_GENRE", "TARGET_TOTAL_WORDS", "MAIN_CHARACTERS", "SUPPORTING_CHARACTERS", "WORLDVIEW_SETTING", "MAIN_PLOT", "NOVEL_INTRO"]
    if any(field not in user_prompt for field in required_fields):
        raise ValueError("user_prompt缺少必要字段")
    # --- 章節分配 ---
    sections = ["第一章節", "第二章節", "第三章節", "第四章節", "第五章節", "第六章節", "第七章節", "第八章節", "第九章節", "第十章節", "第十一章節", "最終章節"]
    # --- 角色描述準備 ---
    main_character_desc = "\n".join([f"姓名：{char.get('name', '未知')}\n角色定位：{char.get('role', '未設定')}\n詳細描述：{char.get('description', '無')}" for char in user_prompt["MAIN_CHARACTERS"]])
    supporting_character_desc = "\n".join([f"姓名：{char.get('name', '未知')}\n角色定位：{char.get('role', '未設定')}\n詳細描述：{char.get('description', '無')}" for char in user_prompt.get("SUPPORTING_CHARACTERS", [])])
    # --- 目錄與日誌設定 ---
    novel_dir = os.path.join(output_dir, user_prompt["NOVEL_NAME"])
    chapters_dir = os.path.join(novel_dir, "章節")
    debug_dir = os.path.join(novel_dir, "debug")
    full_chapter_dir = os.path.join(novel_dir, "總篇章")
    lang_chapter_dir = os.path.join(novel_dir, "總篇章_各語言")
    intro_dir = os.path.join(novel_dir, "故事介紹")
    for dir_path in [novel_dir, chapters_dir, debug_dir, full_chapter_dir, lang_chapter_dir, intro_dir]:
        os.makedirs(dir_path, exist_ok=True)
    debug_file_path = os.path.join(debug_dir, "debug.txt")
    with open(debug_file_path, "w", encoding="utf-8") as f:
        f.write(f"--- 《{user_prompt['NOVEL_NAME']}》生成日誌 ---\n")
    def log_debug(message):
        print(message)
        with open(debug_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{message}\n")
    log_debug(f"小說核心設定：\n{json.dumps(user_prompt, ensure_ascii=False, indent=2)}")
    # --- 類型對應表 ---
    genre_map = {
        "懸疑推理": { "zh-TW": {"title": "《懸疑推理》有聲小說", "description": "此播放清單為《懸疑推理》有聲小說"}, "en": {"title": "《Mystery Thriller》Audiobook", "description": "This playlist is the audiobook of 《Mystery Thriller》"}, "es": {"title": "《Misterio y Suspense》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Misterio y Suspense》"}},
        "網遊": { "zh-TW": {"title": "《網遊》有聲小說", "description": "此播放清單為《網遊》有聲小說"}, "en": {"title": "《Online Game》Audiobook", "description": "This playlist is the audiobook of 《Online Game》"}, "es": {"title": "《Juego Online》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Juego Online》"}},
        "星際": { "zh-TW": {"title": "《星際》有聲小說", "description": "此播放清單為《星際》有聲小說"}, "en": {"title": "《Interstellar》Audiobook", "description": "This playlist is the audiobook of 《Interstellar》"}, "es": {"title": "《Interestelar》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Interestelar》"}},
        "機甲": { "zh-TW": {"title": "《機甲》有聲小說", "description": "此播放清單為《機甲》有聲小說"}, "en": {"title": "《Mecha》Audiobook", "description": "This playlist is the audiobook of 《Mecha》"}, "es": {"title": "《Mecha》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Mecha》"}},
        "異世界": { "zh-TW": {"title": "《異世界》有聲小說", "description": "此播放清單為《異世界》有聲小說"}, "en": {"title": "《Isekai》Audiobook", "description": "This playlist is the audiobook of 《Isekai》"}, "es": {"title": "《Mundo Alternativo》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Mundo Alternativo》"}},
        "搞笑": { "zh-TW": {"title": "《搞笑》有聲小說", "description": "此播放清單為《搞笑》有聲小說"}, "en": {"title": "《Comedy》Audiobook", "description": "This playlist is the audiobook of 《Comedy》"}, "es": {"title": "《Comedia》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Comedia》"}},
        "恐怖": { "zh-TW": {"title": "《恐怖》有聲小說", "description": "此播放清單為《恐怖》有聲小說"}, "en": {"title": "《Horror》Audiobook", "description": "This playlist is the audiobook of 《Horror》"}, "es": {"title": "《Terror》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Terror》"}},
        "都市異能": { "zh-TW": {"title": "《都市異能》有聲小說", "description": "此播放清單為《都市異能》有聲小說"}, "en": {"title": "《Urban Supernatural》Audiobook", "description": "This playlist is the audiobook of 《Urban Supernatural》"}, "es": {"title": "《Urban Supernatural》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Urban Supernatural》"}},
        "末日求生": { "zh-TW": {"title": "《末日求生》有聲小說", "description": "此播放清單為《末日求生》有聲小說"}, "en": {"title": "《Doomsday Survival》Audiobook", "description": "This playlist is the audiobook of 《Doomsday Survival》"}, "es": {"title": "《Supervivencia Apocalíptica》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Supervivencia Apocalíptica》"}},
        "都市修仙": { "zh-TW": {"title": "《都市修仙》有聲小說", "description": "此播放清單為《都市修仙》有聲小說"}, "en": {"title": "《Urban Cultivation》Audiobook", "description": "This playlist is the audiobook of 《Urban Cultivation》"}, "es": {"title": "《Cultivo Urbano》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Cultivo Urbano》"}},
        "霸道總裁": { "zh-TW": {"title": "《霸道總裁》有聲小說", "description": "此播放清單為《霸道總裁》有聲小說"}, "en": {"title": "《Dominant CEO》Audiobook", "description": "This playlist is the audiobook of 《Dominant CEO》"}, "es": {"title": "《CEO Dominante》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《CEO Dominante》"}},
        "青春": { "zh-TW": {"title": "《青春》有聲小說", "description": "此播放清單為《青春》有聲小說"}, "en": {"title": "《Youth》Audiobook", "description": "This playlist is the audiobook of 《Youth》"}, "es": {"title": "《Juventud》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Juventud》"}},
        "輕小說": { "zh-TW": {"title": "《輕小說》有聲小說", "description": "此播放清單為《輕小說》有聲小說"}, "en": {"title": "《Light Novel》Audiobook", "description": "This playlist is the audiobook of 《Light Novel》"}, "es": {"title": "《Novela Ligera》Audiolibro", "description": "Esta lista de reproducción es el audiolibro de 《Novela Ligera》"}},
    }
    # --- 生成多語言故事介紹 JSON ---
    first_genre = user_prompt["NOVEL_GENRE"].split(",")[0].strip()
    intro_data = {
        "title": user_prompt["NOVEL_NAME"],
        "description": user_prompt["NOVEL_INTRO"],
        "tags": [genre.strip() for genre in user_prompt["NOVEL_GENRE"].split(",")],
        "novel_playlist_title": genre_map.get(first_genre, genre_map["懸疑推理"])["zh-TW"]["title"],
        "novel_playlist_description": genre_map.get(first_genre, genre_map["懸疑推理"])["zh-TW"]["description"]
    }
    target_langs = {"zh-TW": "繁體中文", "en": "英文", "es": "西班牙語"}
    for lang_code, lang_name in target_langs.items():
        try:
            filename = f"{user_prompt['NOVEL_NAME']}_full_intro_{lang_code}.json" if lang_code != "zh-TW" else f"{user_prompt['NOVEL_NAME']}_full_intro.json"
            if lang_code == "zh-TW":
                translated_data = intro_data
            else:
                translated_data = translate_json_data(intro_data, lang_code)
                translated_data["novel_playlist_title"] = genre_map.get(first_genre, genre_map["懸疑推理"])[lang_code]["title"]
                translated_data["novel_playlist_description"] = genre_map.get(first_genre, genre_map["懸疑推理"])[lang_code]["description"]
            file_path = os.path.join(intro_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=4)
            log_debug(f" > 已成功生成{lang_name} JSON檔案：{filename}")
        except Exception as e:
            log_debug(f" > [錯誤] 生成{lang_name} JSON時發生錯誤: {e}")
    # --- Prompt模板擴充為12章 ---
    prompt_templates = {
    "第一章節": """
【創作指令】
生成小說第一章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約8.33%。
【本章節任務】
{TASK_DESCRIPTION}
【當前故事狀態】
{STORY_STATE}
【最終指令】
生成第一章節正文，從核心設定開始創作，確保劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第二章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第二章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約16.67%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第二章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第三章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第三章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約25%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第三章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第四章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第四章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約33.33%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第四章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第五章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第五章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約41.67%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第五章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第六章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第六章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約50%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第六章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第七章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第七章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約58.33%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第七章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第八章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第八章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約66.67%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第八章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第九章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第九章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約75%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第九章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第十章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第十章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約83.33%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第十章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "第十一章節": """
【創作指令】
基於之前的小說正文內容，續寫小說第十一章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約91.67%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫第十一章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝。輸出僅限故事正文，無標題或非故事內容。
""",
    "最終章節": """
【創作指令】
基於之前的小說正文內容，續寫小說最終章節正文，生成豐富詳細的內容，避免過短，佔故事總進度的約100%。
【本章節任務】
{TASK_DESCRIPTION}
【前一章內容】
{PREV_CONTENT}
【當前故事狀態】
{STORY_STATE}
【最終指令】
續寫最終章節正文，開頭需平滑銜接前章最後事件，確保與前文銜接，劇情連貫且引人入勝，完整結束故事。輸出僅限故事正文，無標題或非故事內容。
"""
}

    system_prompt = """
你是一位網文作家，擅長根據不同類型創作讓年輕讀者沉浸其中的短篇故事。請嚴格遵循以下創作規則，基於【小說核心設定】主動規劃和創作故事，確保所有元素（如情節、角色互動、世界細節）都與設定高度一致，並適應小說類型。強調故事邏輯性，避免重複情節。
1. **核心原則** - 故事的核心驅動力是角色的成長軌跡，展現主角在故事中的變化或進步。事件需邏輯連貫，如現實般逐步自然展開，避免突兀發展，讓讀者產生強烈代入感。
2. **敘事手法** - 以「互動」展現角色 
2-1. **對話優先**  ： 大量使用角色對話推進劇情、塑造性格、揭示關係。讓對話接地氣且文化適應，融入幽默或張力。
2-2  **精簡內心戲** : 僅在關鍵決策或情緒轉折使用簡短內心獨白，避免過長。
3. **情節結構** - 必須整合【本章節任務】：將其作為創作藍圖，確保本章推進總故事進度。
4. **語言風格** - 使用自然、接地氣的口語化表達，適合年輕讀者，融入中文文化元素。語言優美、生動，避免重複詞彙。
5. **結尾規則** - 章節結尾禁止總結性語句，保持流動性（最終章除外，需完整結束故事，無懸念，並反思成長）。
6. **圓滿結局** - 最終章解決核心劇情，展示主角最終成長，給予滿足感。(非最終章請忽略此項)
7. **前文銜接** - 嚴格參考 【前一章內容】 和 【當前故事狀態】，確保劇情、角色性格和世界觀連貫。避免矛盾，平滑過渡。
【小說核心設定】
- 小說名稱：{NOVEL_NAME}
- 類型：{NOVEL_GENRE}
- 世界觀設定：{WORLDVIEW_SETTING}
- 主線劇情：{MAIN_PLOT}
- 主角設定：{main_character_desc}
- 配角設定：{supporting_character_desc}
"""   
    

    # --- 主流程開始 ---
    task_descriptions = generate_task_descriptions(user_prompt, client)
    if not task_descriptions:
        print("無法生成劇本大綱，小說生成中止。")
        return None
    full_content = []
    story_state = None  # 初始故事狀態為None，將由第一章後更新
    previous_section_content = None  # 前一章內容初始為None
   
    for section_name in sections:
        print(f"正在生成小說{section_name}...")
       
       
        print(f" > 生成{section_name}，生成豐富內容...")
       
        task_desc = task_descriptions.get(section_name, "自由發揮，推進劇情。")
       
        user_messages = prompt_templates[section_name].format(
            TASK_DESCRIPTION=task_desc,
            PREV_CONTENT=previous_section_content if previous_section_content else "無（這是小說開端）",
            STORY_STATE=story_state if story_state else "無（初始狀態，從核心設定開始）"
        )
       
        messages = [
            {"role": "system", "content": system_prompt.format(
                NOVEL_NAME=user_prompt['NOVEL_NAME'],
                NOVEL_GENRE=user_prompt['NOVEL_GENRE'],
                WORLDVIEW_SETTING=user_prompt['WORLDVIEW_SETTING'],
                MAIN_PLOT=user_prompt['MAIN_PLOT'],
                main_character_desc=main_character_desc,
                supporting_character_desc=supporting_character_desc
            )},
            {"role": "user", "content": user_messages}
        ]
       
        log_debug(f" > 為[{section_name}]生成的Prompt Token估計：{sum(len(json.dumps(msg, ensure_ascii=False)) * 1.5 for msg in messages):.0f}")
        params = {
            "model": AI_MODEL,
            "messages": messages,
            "max_tokens": 65536, # 大幅增加以支持高品質長輸出
            "temperature": 0.8, # 平衡創意與一致性
            "top_p": 0.95, # 增加多樣性
            "seed": global_seed
        }
        max_retries = 10 # 增加重試次數以確保品質
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                completion = client.chat.completions.create(**params)
                end_time = time.time()
                content = completion.choices[0].message.content.strip()
               
                content = translate_english_parts(content, translator_en_to_zh)
                content = re.sub(r'^\s*#.*?\n', '', content, flags=re.MULTILINE).strip()
               
                # 移除字數結尾及任何殘留元詞（如爽點、爽）
                content = re.sub(r'\s*\（字數：\d+\）\s*$', '', content, flags=re.MULTILINE).strip()
                content = re.sub(r'\b(爽點|爽|第一個爽點|爽快的)\b', '', content, flags=re.IGNORECASE).strip()
               
                section_path = os.path.join(chapters_dir, f"{section_name}.txt")
                with open(section_path, "w", encoding="utf-8") as f:
                    f.write(content)
                full_content.append(content)
                # 更新故事狀態
                story_state = update_story_state(client, story_state, content, user_prompt)
                previous_section_content = content  # 更新前一章內容為當前章
                log_debug(f" > 已生成{section_name}，耗時: {end_time - start_time:.2f}s，實際字數: {len(content)}，tokens估計: {completion.usage.total_tokens}")
                log_debug(f" > 更新後的故事狀態：{story_state}")
                break
               
            except Exception as e:
                log_debug(f" > [錯誤] 生成{section_name}失敗 (嘗試{attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    log_debug(f"!!!!!!!! [嚴重錯誤] {section_name}生成失敗，終止 !!!!!!!!")
                    return None
                time.sleep(3) # 延長等待時間
        time.sleep(2) # 章節間稍長間隔
   
    # --- 合併與保存 ---
    full_novel_path = os.path.join(full_chapter_dir, f"{user_prompt['NOVEL_NAME']}_full.txt")
    with open(full_novel_path, "w", encoding="utf-8") as f:
        f.write("\n\n\n".join(full_content))
    # --- 生成繁體中文副本 ---
    lang_file_name = f"{user_prompt['NOVEL_NAME']}_full_繁體中文.txt"
    lang_file_path = os.path.join(lang_chapter_dir, lang_file_name)
    shutil.copy(full_novel_path, lang_file_path)
    print(f"小說生成完成，輸出路徑：{full_novel_path}")
    return full_novel_path

# ==============================================================================
# --- 主執行流程 ---
# ==============================================================================

def run_novel_generation_pipeline():
    """主執行流程函數，單次生成小說"""
    current_file_path = os.path.abspath(__file__)
    current_folder_path = os.path.dirname(current_file_path)
    env_path = os.path.join(current_folder_path, 'XAI_API_KEY.env')
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("XAI_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    print("開始生成小說...")
    user_prompt_config, config_path, global_seed = generate_user_prompt_config(client, BASE_OUTPUT_DIR)

    if user_prompt_config:
        novel_path = generate_novel(user_prompt_config, BASE_OUTPUT_DIR)
        print(f"小說配置生成完成，配置文件：{config_path}")
        print(f"小說生成完成，小說文件：{novel_path}")
        return user_prompt_config, config_path, novel_path
    else:
        print("無法生成user_prompt_config，小說生成中止。")
        return None, None, None

if __name__ == "__main__":
    run_novel_generation_pipeline()
