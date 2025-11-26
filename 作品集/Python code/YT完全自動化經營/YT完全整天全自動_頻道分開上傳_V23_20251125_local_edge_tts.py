import os
import json
import shutil
import time
import random
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import ssl
# import openai # OpenAI client will be initialized later
import requests
# from googletrans import Translator # Replaced by deep_translator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydub import AudioSegment
import psutil
import charset_normalizer
from tqdm import tqdm
import ffmpeg # Used by step4 and subtitle generator
from multiprocessing import Pool
# import ai_api # Assuming this is a custom module, ensure it's available
import glob
import sys
import tempfile
from dotenv import load_dotenv
from openai import OpenAI # For OpenAI API
from deep_translator import GoogleTranslator
from datetime import datetime, timedelta # timedelta for subtitle generator
from typing import List, Tuple
# --- Dependencies for Subtitle Generation ---
from faster_whisper import WhisperModel
import srt as srt_lib # Renamed to avoid conflict if 'srt' is used elsewhere
from opencc import OpenCC # 用於簡繁轉換
import torch
# --- End Subtitle Generation Dependencies ---
import concurrent.futures
import os
from pathlib import Path
import chardet
import hanzidentifier
import time
import signal
import sys
from deep_translator import GoogleTranslator as DeepGoogleTranslator
import difflib
import 自動化極短篇小說測試V31_20251117 # Assuming this is your custom module
import faulthandler
faulthandler.enable()
import os
import re
import difflib
import glob
from dataclasses import dataclass
from datetime import timedelta
from zhconv import convert  # 用於簡繁轉換
import re
import difflib
from typing import List, Tuple, Optional
import re
import difflib
from typing import List, Tuple, Optional
import jieba
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import concurrent.futures


def get_next_upload_window_start():
    """計算距離現在最近的下一個上傳窗口開始時間（支援跨夜）"""
    now = datetime.now(TAIWAN_TZ)
    candidates = []
    
    for lang, (start_h, end_h) in UPLOAD_SCHEDULE.items():
        today_start = now.replace(hour=start_h, minute=0, second=0, microsecond=0)
        if end_h <= start_h:  # 跨夜窗口
            if now.hour >= start_h or now.hour < end_h:
                # 正在窗口內，或已經過了 start_h 但還沒到 end_h（理論上不會）
                candidates.append(today_start)
            else:
                # 已經錯過今天的跨夜窗口 → 明天
                tomorrow_start = today_start + timedelta(days=1)
                candidates.append(tomorrow_start)
        else:
            # 同一天窗口
            if now < today_start.replace(hour=end_h):
                candidates.append(today_start)
            else:
                candidates.append(today_start + timedelta(days=1))
    
    if not candidates:
        return now.replace(hour=PRODUCTION_START_HOUR, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    next_time = min(candidates)
    return next_time if next_time > now else next_time + timedelta(days=1)



TAIWAN_TZ = ZoneInfo("Asia/Taipei")

SHUTDOWN_REQUESTED = False # <--- 新增此行

translation_cache = {}

# 中斷標誌
interrupted = False

def graceful_shutdown_handler(sig, frame):
    """處理 Ctrl+C 優雅關機請求"""
    global SHUTDOWN_REQUESTED
    if SHUTDOWN_REQUESTED:
        print("已接收到第二次中斷信號，將強制退出...")
        sys.exit(1)
    SHUTDOWN_REQUESTED = True
    print("\n\n" + "="*50)
    print("【系統】已請求關機。")
    print("將會完成今天所有的生產與排程任務，然後自動終止。")
    print("請耐心等候，或再次按下 Ctrl+C 強制退出。")
    print("="*50 + "\n")


def step1_5_signal_handler(sig, frame):
    """處理 Ctrl+C 中斷信號"""
    global interrupted
    interrupted = True
    print("檢測到中斷信號，正在終止處理...")
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, step1_5_signal_handler)

def step1_5_detect_encoding(file_path):
    """檢測檔案編碼"""
    try:
        with open(file_path, 'rb') as file:
            return chardet.detect(file.read())['encoding']
    except Exception as e:
        print(f"檢測檔案編碼失敗: {file_path}, 錯誤: {e}")
        return 'utf-8'

def step1_5_convert_to_utf8(file_path):
    """讀取檔案並轉換為 UTF-8 編碼，不修改原始檔案"""
    encoding = step1_5_detect_encoding(file_path)
    try:
        with open(file_path, 'rb') as file:
            content = file.read().decode(encoding, errors='replace')
        return True, content
    except Exception as e:
        print(f"轉換為 UTF-8 失敗: {file_path}, 錯誤: {e}")
        return False, None

def step1_5_has_chinese(text):
    """檢查是否包含中文"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)

def step1_5_create_language_copy(file_path, target_langs, sex_voice):
    """生成語言副本檔案"""
    input_path = Path(file_path)
    base_dir = input_path.parent.parent
    lang_dir = base_dir / '總篇章_各語言'
    lang_dir.mkdir(exist_ok=True)
    base_name = input_path.stem
    custom_name = target_langs.get('zh-CN', {}).get('custom_name', '繁體中文')
    new_file_path = lang_dir / f"{base_name}_{custom_name}_{sex_voice}.txt"
    
    if not new_file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as src, \
                 open(new_file_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            print(f"生成語言副本: {new_file_path}")
        except Exception as e:
            print(f"生成語言副本失敗: {new_file_path}, 錯誤: {e}")
    
    return str(new_file_path)

def find_last_sentence_end(text, max_length):
    """查找文本中最後一個句末標點的位置"""
    sentence_end_marks = r'[。！？]'
    matches = [m.start() for m in re.finditer(sentence_end_marks, text[:max_length])]
    if matches:
        return matches[-1] + 1
    return max_length

def step1_5_split_text(text, max_length=1500):
    """將文本按換行符分割並合併至接近 max_length 的段落，確保語句完整"""
    original_paragraphs = text.split('\n')
    segments = []
    current_segment = []
    current_length = 0
    
    for paragraph in original_paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph_length = len(paragraph)
        
        if current_length + paragraph_length <= max_length:
            current_segment.append(paragraph)
            current_length += paragraph_length
        else:
            if current_segment:
                segment_text = '\n'.join(current_segment)
                if len(segment_text) > max_length:
                    cut_pos = find_last_sentence_end(segment_text, max_length)
                    segment_text = segment_text[:cut_pos]
                segments.append(segment_text)
                print(f"分割段落: {segment_text[:20]}... (長度: {len(segment_text)})")
            current_segment = [paragraph]
            current_length = paragraph_length
    
    if current_segment:
        segment_text = '\n'.join(current_segment)
        if len(segment_text) > max_length:
            cut_pos = find_last_sentence_end(segment_text, max_length)
            segment_text = segment_text[:cut_pos]
        segments.append(segment_text)
        print(f"分割段落: {segment_text[:20]}... (長度: {len(segment_text)})")
    
    return segments

def step1_5_check_translation_quality(translated_text):
    """檢查翻譯質量，檢測重複單詞、異常模式和空內容"""
    if not translated_text.strip():
        print("翻譯結果為空內容")
        return False
    
    words = translated_text.split()
    for i in range(len(words) - 4):
        if words[i] == words[i+1] == words[i+2] == words[i+3] == words[i+4]:
            print(f"檢測到連續重複單詞: {words[i]}")
            return False
    
    if re.search(r'\b(\w+)(?:-\1){3,}\b', translated_text, re.IGNORECASE):
        print(f"檢測到異常重複模式: {translated_text[:50]}...")
        return False
    
    return True

def step3_ai_translate_segment(segment, lang_code):
    """使用 Grok 3 API 進行字面翻譯"""
    try:
        current_file_path = os.path.abspath(__file__)
        current_folder_path = os.path.dirname(current_file_path)
        env_path = os.path.join(current_folder_path, 'XAI_API_KEY.env')
        load_dotenv(dotenv_path=env_path)
        api_key = os.getenv("XAI_API_KEY")
        
        if not api_key:
            print("未找到 XAI_API_KEY 環境變數")
            return segment
        
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        
        system_prompt = f"""
        你是一位專業的翻譯專家，負責將中文文本翻譯為 {lang_code} 語言。
        請進行字面翻譯（literal translation），嚴格保留原文的語意和表達，
        不進行語氣、風格或文化背景的適應或修飾。
        僅輸出翻譯結果，不添加任何額外說明或內容。
        """
        
        user_prompt = f"請翻譯以下段落：\n{segment}"
        
        response = client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2500,
            temperature=0.7,
            top_p=0.9
        )
        
        translated_text = response.choices[0].message.content.strip()
        print(f"AI 翻譯成功: {segment[:20]}... -> {translated_text[:20]}...")
        return translated_text
    
    except Exception as e:
        print(f"AI 翻譯失敗: {segment[:50]}..., 錯誤: {e}")
        return segment

def step1_5_translate_segment(segment, lang_code):
    """翻譯單個段落，帶緩存和重試，必要時使用 AI 翻譯"""
    global interrupted
    cache_key = (segment, lang_code, 'zh-CN')
    if cache_key in translation_cache:
        print(f"從快取中獲取翻譯: {segment[:20]}... -> {lang_code}")
        return translation_cache[cache_key]
    
    translator = GoogleTranslator(source='zh-CN', target=lang_code)
    attempt = 0
    max_retries = 5
    while attempt < max_retries:
        if interrupted:
            return segment
        try:
            print(f"正在翻譯段落至 {lang_code} (source: zh-CN): {segment[:20]}...")
            translated_text = translator.translate(segment)
            if step1_5_check_translation_quality(translated_text):
                translation_cache[cache_key] = translated_text
                print(f"Google 翻譯成功: {translated_text[:20]}...")
                return translated_text
            else:
                print(f"Google 翻譯質量不佳，嘗試使用 AI 翻譯: {segment[:50]}...")
                ai_translated_text = step3_ai_translate_segment(segment, lang_code)
                if step1_5_check_translation_quality(ai_translated_text):
                    translation_cache[cache_key] = ai_translated_text
                    return ai_translated_text
                else:
                    print(f"AI 翻譯質量仍不佳，返回原始內容: {segment[:50]}...")
                    attempt += 1
                    time.sleep(min(5 * (2 ** attempt), 60))
        except Exception as e:
            print(f"Google 翻譯失敗: {e}, 重試次數: {attempt + 1}")
            attempt += 1
            time.sleep(min(5 * (2 ** attempt), 60))
    
    print(f"超過 {max_retries} 次重試仍失敗，返回原始內容: {segment[:50]}...")
    return segment

def step1_5_translate_file(input_file_path, sex_voice, pbar_file):
    """翻譯單個檔案"""
    global interrupted
    target_langs = {
        'zh-CN': {'name': 'simplified_chinese', 'custom_name': '繁體中文'},
        'en': {'name': 'english', 'custom_name': '英文'},
        'es': {'name': 'spanish', 'custom_name': '西班牙語'},
    }
    
    success, original_text = step1_5_convert_to_utf8(input_file_path)
    pbar_file.update(1)
    if not success:
        return
    
    step1_5_create_language_copy(input_file_path, target_langs, sex_voice)
    pbar_file.update(1)
    
    input_path = Path(input_file_path)
    base_dir = input_path.parent.parent
    base_name = input_path.stem
    segments = step1_5_split_text(original_text)
    
    for lang_code, lang_info in target_langs.items():
        if interrupted:
            break
        if lang_code == 'zh-CN':
            print(f"目標語言 {lang_code} 與來源語言相同，跳過翻譯")
            continue
        lang_dir = base_dir / '總篇章_各語言'
        lang_dir.mkdir(exist_ok=True)
        output_file = lang_dir / f"{base_name}_{lang_info['custom_name']}_{sex_voice}.txt"
        partial_output_file = lang_dir / f"{base_name}_{lang_info['custom_name']}_partial_{sex_voice}.txt"
        
        if output_file.exists():
            print(f"檔案已存在，跳過: {output_file}")
            pbar_file.update(len(segments))
            continue
        
        translated_segments = []
        with tqdm(total=len(segments), desc=f"翻譯到 {lang_info['custom_name']}", 
                  unit="段落", leave=False) as pbar_lang:
            for segment in segments:
                if interrupted:
                    break
                try:
                    translated_text = step1_5_translate_segment(segment, lang_code)
                    translated_segments.append(translated_text)
                    pbar_lang.update(1)
                    pbar_file.update(1)
                except Exception as e:
                    print(f"段落翻譯失敗: {segment[:50]}..., 錯誤: {e}")
                    translated_segments.append(segment)
                    pbar_lang.update(1)
                    pbar_file.update(1)
        
        translated_text = '\n\n'.join(translated_segments)
        if interrupted:
            with open(partial_output_file, 'w', encoding='utf-8') as file:
                file.write(translated_text.strip())
            break
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(translated_text.strip())
        print(f"翻譯完成: {output_file}")

def step1_5_find_and_translate_txt_files(folder_path, sex_voice):
    """遍歷資料夾並處理 _full.txt 檔案"""
    global interrupted
    files_to_process = []
    for root, dirs, files in os.walk(folder_path):
        if '總篇章' in dirs:
            total_chapter_path = os.path.join(root, '總篇章')
            for file in os.listdir(total_chapter_path):
                if file.endswith('_full.txt'):
                    files_to_process.append(os.path.join(total_chapter_path, file))

    if not files_to_process:
        print("未找到任何 _full.txt 檔案")
        return

    with tqdm(total=len(files_to_process), desc="處理檔案", unit="檔案") as pbar_files:
        for file_path in files_to_process:
            if interrupted:
                break
            success, original_text = step1_5_convert_to_utf8(file_path)
            if not success:
                continue
            base_steps = 2
            segments = step1_5_split_text(original_text)
            lang_count = 2  # 目標語言數量（英文、西班牙文）
            total_steps = base_steps + len(segments) * lang_count

            with tqdm(total=total_steps, desc=f"處理 {Path(file_path).name}",
                      unit="步驟", leave=False) as pbar_file:
                step1_5_translate_file(file_path, sex_voice, pbar_file)
            pbar_files.update(1)

def step1_5_main(story_folder):
    """
    【修改版】
    此函式會動態決定要使用的語音性別（男聲/女聲）。
    它會讀取故事設定檔，根據主角性別來選擇，如果找不到或設定錯誤，則預設為男聲。
    """
    try:
        story_name = os.path.basename(story_folder)
        sex_voice = "男聲"  # 預設值

        # 1. 構建設定檔的路徑
        # 假設 config 檔案命名規則為 {story_name}_config.json
        config_folder_path = os.path.join(story_folder, "user_prompt_config")
        config_file_path = os.path.join(config_folder_path, f"{story_name}_config.json")

        print(f"【Step 1.5】嘗試讀取性別設定檔: {config_file_path}")

        # 2. 讀取並解析 JSON 檔案
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 3. 提取性別資訊
                gender = config_data.get("MAIN_CHARACTER_GENDER", "").strip()

                # 4. 根據性別決定 voice
                if gender == "女性":
                    sex_voice = "女聲"
                    print(f"【Step 1.5】偵測到主角性別為「女性」，將使用「女聲」。")
                elif gender == "男性":
                    sex_voice = "男聲"
                    print(f"【Step 1.5】偵測到主角性別為「男性」，將使用「男聲」。")
                else:
                    # 防呆機制
                    print(f"【Step 1.5】設定檔中的性別為「{gender}」，非標準值。將預設使用「男聲」。")
                    sex_voice = "男聲"

            except json.JSONDecodeError:
                print(f"【Step 1.5】警告：JSON 檔案格式錯誤，無法解析。將預設使用「男聲」。")
            except Exception as e:
                print(f"【Step 1.5】警告：讀取設定檔時發生錯誤: {e}。將預設使用「男聲」。")
        else:
            # 防呆機制：如果檔案不存在
            print(f"【Step 1.5】警告：找不到性別設定檔。將預設使用「男聲」。")

        # 5. 呼叫翻譯函式，傳入動態決定的 sex_voice
        step1_5_find_and_translate_txt_files(story_folder, sex_voice=sex_voice)

    except KeyboardInterrupt:
        print("【Step 1.5】程式已由使用者手動終止。")
    except Exception as e:
        import traceback
        print(f"【Step 1.5】主流程發生未預期的錯誤: {e}")
        traceback.print_exc()
        
# 全局路徑
BASE_PATH = r"D:\python_store_folder\youtube_video_story"
UPLOADED_PATH = r"D:\已上傳的故事"
IMAGE_FOLDER = r"D:\background_images"


def step2_get_unique_filename(base_path, base_name, extension):
    counter = 1
    while True:
        filename = f"{base_name}_{counter}{extension}"
        full_path = os.path.join(base_path, filename)
        if not os.path.exists(full_path):
            return filename
        counter += 1

# Step 2: 生成縮圖
def step2_main(story_path):
    global client_openai  # Use the global client

    # --- OpenAI API Key Loading ---
    current_file_path = os.path.abspath(__file__)
    current_folder_path = os.path.dirname(current_file_path)

    env_path = os.path.join(current_folder_path, 'OPENAI_API_KEY.env')
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"未找到 {env_path}，請確認文件是否存在且包含 OPENAI_API_KEY=\"sk-...\"")

    load_dotenv(dotenv_path=env_path)

    api_key_openai = os.getenv("OPENAI_API_KEY")
    if not api_key_openai:
        raise ValueError("未找到 OPENAI_API_KEY，請檢查 OPENAI_API_KEY.env 文件內容")
    print(f"載入的 OpenAI API 金鑰：{api_key_openai[:7]}...{api_key_openai[-4:]}（部分隱藏）")
    
    client_openai = OpenAI(api_key=api_key_openai)
    BACKGROUND_PATH = r"D:\background_images"
    # Create background_images directory if it doesn't exist
    if not os.path.exists(BACKGROUND_PATH):
        os.makedirs(BACKGROUND_PATH)

    if os.path.isdir(story_path):
        intro_folder = os.path.join(story_path, "故事介紹")
        print(f"intro_folder: {intro_folder}")
        if os.path.exists(intro_folder):
            for file in os.listdir(intro_folder):
                if file.endswith("_full_intro.json"):
                    json_file_path = os.path.join(intro_folder, file)
                    print(f"json_file_path: {json_file_path}")
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        story_title = data.get("title", "")
                        story_description = data.get("description", "")
                        story_tags = data.get("tags", [])
                        
                        # 提取大約20個中文字，並在標點符號處斷句
                        if len(story_description) > 20:
                            punctuation_marks = "，,。,！,？,；,"
                            for i in range(20, len(story_description)):
                                if story_description[i] in punctuation_marks:
                                    story_description_excerpt = story_description[:i+1]
                                    break
                            else:
                                story_description_excerpt = story_description[:20]
                        else:
                            story_description_excerpt = story_description

                        # 定義 prompt 生成函數
                        def generate_prompt(attempt):
                            if attempt == 1:
                                return f"""
生成一張 16:9 的動漫AI風格圖片，需高度契合以下故事名稱和背景：
- 故事名稱: {story_title}
- 故事背景與主題: {story_description_excerpt}
- 視覺風格要求:
- 確保圖片視覺效果鮮明、生動。
- 確保圖片中無任何文字。
- 場景設計需反映故事的核心元素。
- 角色或場景應具備細膩的細節，符合日式動漫的精緻畫風。
                                """
                            elif attempt == 2:
                                return f"""
生成一張 16:9 的動漫AI風格圖片，需高度契合以下故事名稱：
- 故事名稱: {story_title}
- 視覺風格要求:
- 確保圖片視覺效果鮮明、生動。
- 確保圖片中無任何文字。
- 場景設計需反映故事的核心元素。
- 角色或場景應具備細膩的細節，符合日式動漫的精緻畫風。
                                """
                            elif attempt == 3:
                                tags_str = ", ".join(story_tags)
                                return f"""
生成一張 16:9 的動漫AI風格圖片，需高度契合以下故事標籤：
- 故事標籤: {tags_str}
- 視覺風格要求:
- 確保圖片視覺效果鮮明、生動。
- 確保圖片中無任何文字。
- 場景設計需反映故事的核心元素。
- 角色或場景應具備細膩的細節，符合日式動漫的精緻畫風。
                                """
                            elif attempt == 4:
                                tags_str = ", ".join(story_tags)
                                return f"""
生成一張 16:9 的動漫AI風格隨機圖片，需高度契合以下故事標籤：
- 視覺風格要求:
- 確保圖片視覺效果鮮明、生動。
- 確保圖片中無任何文字。
- 角色或場景應具備細膩的細節，符合日式動漫的精緻畫風。
                                """

                            else:
                                return f"""生成一張 16:9 的動漫AI風格隨機圖片 """

                        # 嘗試生成圖片，最多嘗試3次
                        for attempt in range(1, 5):
                            try:
                                prompt = generate_prompt(attempt)
                                print(f'嘗試 {attempt}: prompt: {prompt}')
                                response = client_openai.images.generate(
                                    model="dall-e-3",
                                    prompt=prompt,
                                    size="1792x1024",
                                    quality="standard",
                                    n=1,
                                    response_format="url"
                                )
                                image_url = response.data[0].url
                                # 保存圖片
                                thumbnail_folder = os.path.join(story_path, "故事_thumbnail_file")
                                if not os.path.exists(thumbnail_folder):
                                    os.makedirs(thumbnail_folder)
                                file_name = "原始圖片.jpg"
                                full_path = os.path.join(thumbnail_folder, file_name)
                                response = requests.get(image_url)
                                if response.status_code == 200:
                                    with open(full_path, 'wb') as f:
                                        f.write(response.content)
                                    print(f"Step 2: 圖片已儲存至: {full_path}")

                                    # Save to background_images folder with unique name
                                    background_filename = step2_get_unique_filename(BACKGROUND_PATH, "image", ".jpg")
                                    background_full_path = os.path.join(BACKGROUND_PATH, background_filename)
                                    with open(background_full_path, 'wb') as f:
                                        f.write(response.content)
                                    print(f"Step 2: 圖片已儲存至背景資料夾: {background_full_path}")
                                    break  # 成功生成圖片，跳出循環
                            except Exception as e:
                                print(f"嘗試 {attempt} 失敗: {e}")
                                if attempt == 3:
                                    print("所有嘗試均失敗，無法生成圖片")

# Step 3: 文字轉語音 (雲端 Edge-TTS 版本，輸出 FLAC)
import os
import re
import time
import asyncio # 引入 asyncio 進行異步操作
import edge_tts # 引入 Edge-TTS 函式庫
import charset_normalizer 
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor # 保留，以防主腳本中仍需用到
import glob # 用於清理臨時檔案

# ----------------- 舊版本地 TTS 相關變數已被移除 -----------------

# ==================== Edge-TTS 模型與穩定性設定區 ====================

# 1. 併發數量設定: 設為 1 以確保最穩健執行，避免服務端限制
MAX_CONCURRENT_TTS = 1 

# 2. 文字塊大小設定: 參考您的建議，設為 800，確保單次請求穩定
CHUNK_SIZE = 800 

# Edge-TTS 語音配置 (沿用您指定的 ID)
# 注意：中文部分使用的是 zh-CN 的 ID，但 Edge-TTS 支援繁體文本輸入
EDGE_TTS_VOICES = {
    "繁體中文": {
        "男聲": {"voice_id": "zh-CN-YunxiNeural", "lang": "zh-CN"},
        "女聲": {"voice_id": "zh-CN-XiaomengNeural", "lang": "zh-CN"}
    },
    "英文": {
        "男聲": {"voice_id": "en-US-ChristopherNeural", "lang": "en-US"},
        "女聲": {"voice_id": "en-AU-TinaNeural", "lang": "en-AU"} # 更改為您指定的 ID
    },
    "西班牙語": {
        "男聲": {"voice_id": "es-MX-JorgeNeural", "lang": "es-MX"},
        "女聲": {"voice_id": "es-MX-DaliaNeural", "lang": "es-MX"}
    }
}

# ==================== 輔助函數 (Edge-TTS 適用) ====================

def step3_detect_encoding(file_path):
    """偵測檔案編碼 (保留原邏輯)"""
    with open(file_path, "rb") as f:
        raw_data = f.read()
    result = charset_normalizer.detect(raw_data)
    encoding = result["encoding"] if result["encoding"] else "utf-8"
    print(f"Detected encoding for {file_path}: {encoding}")
    return encoding

def step3_split_text(text, chunk_size=CHUNK_SIZE):
    """
    分割長文本成 chunks (優化自您的參考程式碼，確保按段落分割且不超限)
    """
    text = text.replace("\r\n", "\n")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = ""
    
    for para in paragraphs:
        if len(para) > chunk_size:
            # 如果單一段落極長，強制按句號或最大長度切分
            sentences = re.split(r'([。？！])', para)
            
            sub_current = ""
            for i in range(0, len(sentences), 2):
                sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                if len(sub_current) + len(sentence) <= chunk_size:
                    sub_current += sentence
                else:
                    if sub_current:
                        chunks.append(sub_current)
                    sub_current = sentence
            if sub_current:
                chunks.append(sub_current)
            continue
            
        if len(current) + len(para) + 1 <= chunk_size:
            current += para + "\n"
        else:
            if current:
                chunks.append(current.rstrip())
            current = para + "\n"
    
    if current:
        chunks.append(current.rstrip())
    
    return chunks

def step3_merge_audio_files_pydub(audio_files, output_path, temp_mp3_files):
    """
    合併多個 MP3 檔案，並轉換成單一 FLAC 輸出 (修正為 FLAC 輸出)
    """
    combined = AudioSegment.empty()
    print(f"開始合併 {len(audio_files)} 個 MP3 片段並轉換為 FLAC...")
    
    # 讀取並合併 MP3
    for mp3_file in audio_files:
        if os.path.exists(mp3_file):
            segment = AudioSegment.from_file(mp3_file, format="mp3")
            # 在片段間加入 100 毫秒靜音，使語音間隔更自然 (可選)
            combined += segment + AudioSegment.silent(duration=100) 

    # 輸出最終檔案為 FLAC
    # 設置編碼參數以確保高音質
    combined.export(output_path, format="flac", parameters=["-acodec", "flac"]) 
    print(f"合併完成 (輸出 FLAC): {output_path}")

    # 清理所有臨時 MP3 檔案 (此處清理只是輔助，最終清理在 finally 塊)
    cleaned_count = 0
    for temp_file in temp_mp3_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                cleaned_count += 1
            except Exception as e:
                # 這裡只是在合併後清理，最終清理邏輯會在 finally 確保
                print(f"Warning: Failed to clean up temp file {temp_file} after merging: {e}") 
    print(f"已清理 {cleaned_count} 個臨時 MP3 檔案 (in-function cleanup)。")


# ----------------- Edge-TTS 核心邏輯 (Async) -----------------

async def step3_process_chunk(sem, i, chunk, voice_id, output_dir):
    """處理單一 chunk 的 Edge-TTS 生成 (使用 async/await)"""
    temp_mp3 = os.path.join(output_dir, f"temp_{i:04d}.mp3")
    
    # 移除可能導致 TTS 錯誤的字符
    chunk = re.sub(r'[\ufeff\u200b]', '', chunk).strip() 
    if not chunk:
        return None

    # 重試機制
    max_retries = 3 
    for attempt in range(max_retries):
        async with sem: # 使用 Semaphore 限制併發數
            try:
                # 建立 TTS 通訊物件
                communicate = edge_tts.Communicate(chunk, voice_id) 
                
                # 異步儲存為 MP3
                await communicate.save(temp_mp3)
                
                # 檢查文件是否真的生成且非空
                if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
                    print(f"Chunk {i:04d} 處理成功: {os.path.basename(temp_mp3)}")
                    return temp_mp3
                else:
                    raise Exception("文件生成為空")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = min(5 * (2 ** attempt), 30)
                    print(f"Chunk {i:04d} 失敗 (嘗試 {attempt+1}/{max_retries}): {e}，等待 {wait_time} 秒...")
                    await asyncio.sleep(wait_time) 
                else:
                    print(f"Chunk {i:04d} 徹底失敗: {e}")
                    return None

def step3_is_valid_flac(file_path):
    """驗證 FLAC 是否有效 (修正為 FLAC 驗證)"""
    try:
        audio = AudioSegment.from_file(file_path, format="flac")
        print(f"FLAC file is valid, duration: {len(audio) / 1000} seconds")
        return True
    except Exception as e:
        print(f"Invalid FLAC file: {file_path}, error: {e}")
        return False

# ----------------- 主執行函數 (需要改成 Async) -----------------

async def step3_main_async(story_folder, story_name):
    """主函數，執行 Edge-TTS 語音生成 (輸出 FLAC)"""
    
    if os.path.isdir(story_folder):
        language_folder = os.path.join(story_folder, "總篇章_各語言")
        if os.path.exists(language_folder):
            
            # 使用 Semaphore 限制併發數
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_TTS)

            for txt_file in os.listdir(language_folder):
                if txt_file.endswith(".txt"):
                    txt_path = os.path.join(language_folder, txt_file)
                    print(f"\n--- 正在處理檔案: {txt_file} ---")

                    parts = txt_file.replace(".txt", "").split("_")
                    if len(parts) >= 2:
                        language = parts[-2]
                        voice_gender = parts[-1]
                    else:
                        print(f"Invalid filename format: {txt_file}, skipping")
                        continue

                    # 初始化變數
                    temp_audio_files = [] 
                    output_dir = os.path.join(story_folder, "故事音檔_flac") 
                    os.makedirs(output_dir, exist_ok=True)

                    try: # <-- 新增：包含所有檔案處理邏輯的主要 try 區塊

                        # 1. 讀取文字 (包含編碼偵測和 fallback)
                        encoding = step3_detect_encoding(txt_path)
                        text = None # 初始化 text 變數
                        
                        # 嘗試用 utf-8 讀取，失敗則用偵測到的編碼
                        try:
                            with open(txt_path, "r", encoding="utf-8") as f:
                                text = f.read()
                        except UnicodeDecodeError:
                            with open(txt_path, "r", encoding=encoding) as f:
                                text = f.read()

                        if not text:
                            raise Exception("Failed to read text content from file.")
                        
                        # 2. 獲取 Edge-TTS 配置
                        if language in EDGE_TTS_VOICES and voice_gender in EDGE_TTS_VOICES[language]:
                            config = EDGE_TTS_VOICES[language][voice_gender]
                            voice_id = config["voice_id"]
                        else:
                            print(f"Unsupported language or gender: {language}_{voice_gender}, skipping.")
                            continue

                        # 3. 設定輸出路徑
                        output_path = os.path.join(output_dir, f"{story_name}_{language}_{voice_gender}.flac")

                        # 如果輸出檔案已存在，跳過
                        if os.path.exists(output_path):
                            print(f"輸出檔案已存在: {output_path}, 跳過 TTS 處理。")
                            continue

                        start_time = time.time()
                        
                        # 4. 切割文本
                        text_chunks = step3_split_text(text, chunk_size=CHUNK_SIZE)
                        print(f"開始生成 {len(text_chunks)} 個音頻 chunks (Voice: {voice_id}, Chunk Size: {CHUNK_SIZE})")

                        # 5. 建立異步任務並執行
                        chunk_tasks = [step3_process_chunk(semaphore, i, chunk, voice_id, output_dir)
                                       for i, chunk in enumerate(text_chunks)]
                        
                        results = await asyncio.gather(*chunk_tasks)
                        
                        # 過濾掉失敗（返回 None）的 chunk
                        temp_audio_files = [res for res in results if res is not None]

                        if temp_audio_files:
                            # 6. 排序
                            def extract_number(filename):
                                # 使用 temp_0000.mp3 的格式排序
                                match = re.search(r'temp_(\d{4})\.mp3', os.path.basename(filename))
                                return int(match.group(1)) if match else float('inf')

                            temp_audio_files.sort(key=extract_number)
                            print(f"Sorted {len(temp_audio_files)} temp files for merging")
                            
                            # 7. 合併 MP3 並轉換為 FLAC (會自行清理列表中的 mp3 檔案)
                            step3_merge_audio_files_pydub(temp_audio_files, output_path, temp_audio_files)

                            # 8. 驗證
                            if step3_is_valid_flac(output_path):
                                elapsed_time = time.time() - start_time
                                print(f"Successfully generated {output_path}, time: {elapsed_time:.2f} seconds")
                            else:
                                # 驗證失敗則拋出錯誤，由外部 except 捕獲
                                raise Exception(f"Invalid FLAC file after merging: {output_path}")
                        else:
                            print(f"警告: {txt_file} 沒有成功生成任何音頻 chunk，跳過合併。")

                    except Exception as e: # <-- 修正後的 except 區塊：捕獲所有處理錯誤
                        print(f"Error processing {txt_path}: {e}")
                    
                    finally: # <-- 修正後的 finally 區塊：確保無論成功或失敗都執行清理
                        # 最終清理：確保清理任何殘留 temp_*.mp3 檔案
                        temp_pattern = os.path.join(output_dir, "temp_*.mp3")
                        for temp_file in glob.glob(temp_pattern):
                            try:
                                os.remove(temp_file)
                            except Exception as e:
                                print(f"清理臨時檔案 {temp_file} 失敗: {e}")


# ----------------- 運行主入口 -----------------

def step3_main(story_folder, story_name):
    """
    Step 3 的主要入口，負責啟動 asyncio 循環來執行 TTS
    """
    print("--- 啟動 Edge-TTS 語音生成程序 ---")
    try:
        # 嘗試使用新的循環執行異步主函數
        asyncio.run(step3_main_async(story_folder, story_name))
    except RuntimeError as e:
        if "cannot run non-async" in str(e):
            print("警告: 檢測到已在異步環境中運行，嘗試使用現有循環。")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(step3_main_async(story_folder, story_name))
        else:
            print(f"發生未預期的 RuntimeError: {e}")
            raise e

# ==================== Step 3 結束 (Edge-TTS FLAC) ====================

# Step 4: 生成 MP4 影片
FPS = 30
FADE_SEC = 1
TARGET_W, TARGET_H = 1920, 1080
WATERMARK_IMAGE = r"D:\python_store_folder\YT_personal_image\logo.jpg"
WATERMARK_SCALE = 0.1
WATERMARK_OPACITY = 0.1

def step4_preprocess_image(image_path, output_folder):
    start_time = time.time()
    if not os.path.exists(image_path):
        print(f"輸入圖片不存在: {image_path}")
        return None
    if not os.path.exists(WATERMARK_IMAGE):
        print(f"浮水印圖片不存在: {WATERMARK_IMAGE}")
        return None
    if not os.access(output_folder, os.W_OK):
        print(f"無權寫入輸出資料夾: {output_folder}")
        return None

    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, os.path.basename(image_path))

    try:
        tmp = os.path.join(tempfile.gettempdir(), f"tmp_pre_{os.path.basename(image_path)}")
        stream = ffmpeg.input(image_path)
        stream = stream.filter('format', 'nv12')
        stream = stream.filter('hwupload_cuda')
        stream = stream.filter('scale_cuda', w=TARGET_W, h=-2, force_original_aspect_ratio='decrease')
        stream = stream.filter('hwdownload')
        stream = stream.filter('format', 'nv12')
        stream = stream.filter('pad', TARGET_W, TARGET_H, '(ow-iw)/2', '(oh-ih)/2')
        stream = stream.output(tmp, pix_fmt='yuv420p', vframes=1)
        stream = stream.global_args('-init_hw_device', 'cuda=cuda:0', '-filter_hw_device', 'cuda')
        stream = stream.overwrite_output()
        stream.run(capture_stderr=True, quiet=False)
    except ffmpeg.Error:
        stream = ffmpeg.input(image_path)
        stream = stream.filter('scale', w='if(gt(a,1920/1080),1920,-1)', h='if(gt(a,1920/1080),-1,1080)', force_original_aspect_ratio='decrease')
        stream = stream.filter('pad', TARGET_W, TARGET_H, '(ow-iw)/2', '(oh-ih)/2')
        stream = stream.output(tmp, pix_fmt='yuv420p', vframes=1)
        stream = stream.overwrite_output()
        stream.run(capture_stderr=True, quiet=False)

    if not os.path.exists(tmp):
        raise RuntimeError(f"FFmpeg 縮放失敗，臨時文件未生成: {tmp}")

    img = cv2.imread(tmp)
    if img is None:
        raise RuntimeError(f"無法讀取臨時圖像: {tmp}")

    watermark = Image.open(WATERMARK_IMAGE).convert('RGBA')
    wm_w, wm_h = watermark.size
    new_wm_w = int(wm_w * WATERMARK_SCALE)
    new_wm_h = int(wm_h * WATERMARK_SCALE)
    if new_wm_w > 0 and new_wm_h > 0:
        watermark = watermark.resize((new_wm_w, new_wm_h), Image.LANCZOS)
    else:
        raise ValueError(f"縮放後的浮水印尺寸無效: {new_wm_w}x{new_wm_h}")

    watermark_data = watermark.split()
    if len(watermark_data) == 4:
        r, g, b, a = watermark_data
        a = a.point(lambda i: i * WATERMARK_OPACITY)
        watermark = Image.merge('RGBA', (r, g, b, a))
    else:
        a = Image.new('L', watermark.size, int(255 * WATERMARK_OPACITY))
        watermark = Image.merge('RGBA', (*watermark_data, a))

    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
    x = (img_pil.width - new_wm_w) // 2
    y = (img_pil.height - new_wm_h) // 2
    output = Image.new('RGBA', img_pil.size)
    output.paste(img_pil, (0, 0))
    output.paste(watermark, (x, y), watermark)
    result = cv2.cvtColor(np.array(output), cv2.COLOR_RGBA2BGR)

    ext = os.path.splitext(output_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        output_path = os.path.splitext(output_path)[0] + '.jpg'
        ext = '.jpg'

    success = False
    if ext in ['.jpg', '.jpeg']:
        _, buf = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    elif ext == '.png':
        _, buf = cv2.imencode('.png', result)
    else:
        raise RuntimeError(f"不支持的圖像格式: {ext}")

    if buf is not None:
        with open(output_path, 'wb') as f:
            f.write(buf.tobytes())
        success = True
    else:
        raise RuntimeError(f"圖像編碼失敗: {output_path}")

    if not success or not os.path.exists(output_path):
        raise RuntimeError(f"保存圖像失敗: {output_path}")

    os.remove(tmp)
    return output_path

step4_effects = ['zoom']

def step4_create_image_segment(args):
    image_path, output_path, duration = args
    start_time = time.time()
    print(f"開始生成影片段: {output_path} (輸入: {image_path}, 時長: {duration}s)")

    if not os.path.exists(image_path) or duration <= 0:
        print(f"圖像不存在或時長無效: {image_path}, {duration}")
        return None

    d = int(duration * FPS)
    step4_effect = random.choice(step4_effects)
    fade_in = f"fade=t=in:st=0:d={FADE_SEC}"
    fade_out = f"fade=t=out:st={max(0, duration-FADE_SEC-0.1)}:d={FADE_SEC}"

    if step4_effect == 'zoom':
        zoompan = f"zoompan=z='zoom+0.0002':s={TARGET_W}x{TARGET_H}:fps={FPS}:d={d}"
        filter_complex = f"{zoompan},{fade_in},{fade_out},format=yuv420p"
    else:
        raise ValueError(f"未知的特效: {step4_effect}")

    cmd_nvenc = [
        "ffmpeg", "-y", "-init_hw_device", "cuda=cuda:0", "-filter_hw_device", "cuda",
        "-loop", "1", "-framerate", str(FPS), "-i", image_path, "-vf", filter_complex,
        "-t", str(duration), "-c:v", "h264_nvenc", "-b:v", "5M", "-preset", "p2",
        "-pix_fmt", "yuv420p", "-r", str(FPS), output_path
    ]
    try:
        subprocess.run(cmd_nvenc, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"[segment] {output_path} (NVENC, 耗時: {time.time() - start_time:.2f}s)")
        return output_path
    except subprocess.CalledProcessError:
        cmd_libx264 = [
            "ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", image_path,
            "-vf", filter_complex, "-t", str(duration), "-c:v", "libx264", "-b:v", "5M",
            "-pix_fmt", "yuv420p", "-r", str(FPS), output_path
        ]
        subprocess.run(cmd_libx264, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return output_path

def step4_create_video_with_images(flac_file, output_mp4, image_folder, processed_image_folder):
    start_time = time.time()
    print(f"開始生成影片: {output_mp4} (音頻: {flac_file})")

    probe = ffmpeg.probe(flac_file)
    duration = float(probe['format']['duration'])
    print(f"音頻時長: {duration:.2f}s")

    if os.path.exists(processed_image_folder):
        shutil.rmtree(processed_image_folder)
    os.makedirs(processed_image_folder)

    if not os.path.exists(image_folder):
        print(f"圖片資料夾不存在: {image_folder}")
        return
    imgs = glob.glob(os.path.join(image_folder, "*.[jp][pn]g"))
    if not imgs:
        print(f"未在 {image_folder} 中找到任何圖片")
        return
    imgs = [step4_preprocess_image(p, processed_image_folder) for p in imgs]
    imgs = [p for p in imgs if p]
    if not imgs:
        print("沒有可用圖片")
        return

    random.shuffle(imgs)
    print(f"圖片順序已隨機打亂，共 {len(imgs)} 張圖片")

    per = 10.0
    full = int(duration // per)
    rem = duration - full * per
    seg_durs = [per] * full + ([rem] if rem > 0.5 else [])

    tasks = [(imgs[idx % len(imgs)], f"seg_{idx}.mp4", dur) for idx, dur in enumerate(seg_durs)]
    temp_files = [task[1] for task in tasks]

    with Pool(processes=8) as pool:
        segs = pool.map(step4_create_image_segment, tasks)
    segs = [s for s in segs if s]
    if not segs:
        print("所有段落生成失敗，檢查 FFmpeg 命令或圖像文件")
        return

    concat_file = "concat.txt"
    with open(concat_file, "w", encoding='utf-8') as f:
        for s in segs:
            f.write(f"file '{s}'\n")

    audio_input = ffmpeg.input(flac_file)
    ffmpeg.input(concat_file, format='concat', safe=0).output(
        audio_input, output_mp4, vcodec='copy', acodec='aac',
        audio_bitrate='128k', t=duration, fflags='+genpts', map_metadata='-1'
    ).overwrite_output().run(quiet=True)

    for f in temp_files + [concat_file]:
        if os.path.exists(f):
            os.remove(f)
    print(f"[done] {output_mp4} (耗時: {time.time() - start_time:.2f}s)")

def step4_main(story_path):
    flac_dir = os.path.join(story_path, "故事音檔_flac")
    mp4_dir = os.path.join(story_path, "故事影片_mp4")
    ffmpeg_path = r"C:\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"
    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
        print(f"FFmpeg 路徑已設置: {ffmpeg_path}")
    else:
        print(f"FFmpeg 未找到: {ffmpeg_path}")
        return
    os.makedirs(mp4_dir, exist_ok=True)
    processed = os.path.join(IMAGE_FOLDER, "processed_images")
    for flac_file in os.listdir(flac_dir):
        if flac_file.endswith('.flac'):
            flac_path = os.path.join(flac_dir, flac_file)
            mp4_path = os.path.join(mp4_dir, flac_file.replace('.flac', '.mp4'))
            print(f"Step 4: 生成 MP4 {mp4_path}")
            step4_create_video_with_images(flac_path, mp4_path, IMAGE_FOLDER, processed)



import os
import re
import time
import subprocess
import shutil
import torch
import ffmpeg
import srt as srt_lib
from dataclasses import dataclass
from datetime import timedelta
from opencc import OpenCC
from faster_whisper import WhisperModel
import spacy
import difflib
import jieba
from typing import List, Tuple, Optional


# 定義字幕物件類 (用於 whisper 輸出)
@dataclass
class Subtitle:
    index: int
    start: str
    end: str
    content: str

# --- Subtitle Generation Configuration ---
WHISPER_MODEL_SIZE = "turbo"  # 可選: "tiny", "base", "small", "medium", "large-v2", "large-v3"
FFMPEG_PATH_SUBGEN = r"C:\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"  # 請確認此路徑有效
PREFERRED_FONT_SUBGEN = "Noto Sans TC"  # 例如用於繁體中文

language_mapping = {
    "繁體中文": "zh",
    "英文": "en",
    "西班牙語": "es"
}

# --- Initialize OpenCC Converter for Subtitle Generation ---
try:
    converter_s2twp_subgen = OpenCC('s2twp')  # 簡體到台灣正體 (包含詞彙轉換)
except Exception as e:
    print(f"初始化 OpenCC 失敗: {e}")
    print("請確保已安裝 opencc-python-reimplemented 並擁有正確的配置文件。")
    print("可以使用 'pip install opencc-python-reimplemented' 命令安裝。")
    converter_s2twp_subgen = None

# 加載中文 NER 模型
try:
    nlp = spacy.load("zh_core_web_sm")
except Exception as e:
    print(f"載入 spacy 中文模型失敗: {e}")
    print("請確保已安裝模型，可使用 'python -m spacy download zh_core_web_sm' 安裝")
    nlp = None

def step4_5_subgen_convert_to_traditional_chinese(text):
    """將文本從繁體中文轉換為繁體中文 (字幕生成用)"""
    if converter_s2twp_subgen and text:
        try:
            return converter_s2twp_subgen.convert(text)
        except Exception as e:
            print(f"OpenCC 轉換失敗: {e}，返回原文。")
            return text
    return text

def step4_5_subgen_format_ass_time(td: timedelta) -> str:
    """將 timedelta 對象轉換為 ASS 時間格式 H:MM:SS.cc (字幕生成用)"""
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    centiseconds = int(round((total_seconds - int(total_seconds)) * 100))
    
    if centiseconds == 100:
        centiseconds = 0
        seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
    return f"{hours:01}:{minutes:02}:{seconds:02}.{centiseconds:02}"

def split_into_sentences(text, language_code):
    """根據語言將文本分割為句子"""
    if not text:
        return []
    if language_code == "zh":
        sentences = re.split(r'([。？！，…——：])', text)
        result = []
        current_sentence = ""
        for i in range(0, len(sentences), 2):
            part = sentences[i]
            if i + 1 < len(sentences):
                part += sentences[i + 1]
            current_sentence += part
            if i + 1 < len(sentences) and sentences[i + 1] in '。？！…' or len(current_sentence) > 40:
                result.append(current_sentence.strip())
                current_sentence = ""
        if current_sentence.strip():
            result.append(current_sentence.strip())
        return [s for s in result if s]
    else:
        sentences = re.split(r'([.?!])(?=\s|$|[A-Z])', text)
        result = []
        current_sentence = ""
        for i in range(0, len(sentences), 2):
            part = sentences[i]
            if i + 1 < len(sentences):
                part += sentences[i + 1]
            current_sentence += part.strip()
            if i + 1 < len(sentences) and sentences[i + 1] in '.?!':
                result.append(current_sentence.strip())
                current_sentence = ""
        if current_sentence.strip():
            result.append(current_sentence.strip())
        return [s for s in result if s]

def split_long_subtitle(text, max_length, language_code):
    """將長字幕分割為多行，結合語義分割和字數限制"""
    if not text:
        return []
        
    sentences = split_into_sentences(text, language_code)
    lines = []
    
    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if not sentence_stripped:
            continue
        if len(sentence_stripped) <= max_length:
            lines.append(sentence_stripped)
        else:
            if language_code == "zh":
                sub_sentences = re.split(r'([，—])', sentence_stripped)
                current_line = ""
                for i in range(0, len(sub_sentences), 2):
                    part = sub_sentences[i]
                    if i + 1 < len(sub_sentences):
                        part += sub_sentences[i + 1]
                    if len(current_line) + len(part) <= max_length:
                        current_line += part
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = part
                if current_line:
                    lines.append(current_line.strip())
            else:
                words = sentence_stripped.split()
                current_line = ""
                for word in words:
                    needs_space = current_line != ""
                    if len(current_line) + len(word) + (1 if needs_space else 0) <= max_length:
                        current_line += (" " if needs_space else "") + word
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word
                if current_line:
                    lines.append(current_line.strip())
    
    return [line for line in lines if line]

def step4_5_subgen_convert_srt_to_ass(srt_path, ass_path, preferred_font, font_size_param, language_code,
                                      primary_color="&H00FFFFFF&", secondary_color="&H00FFFFFF&",
                                      outline_color="&H00000000&", back_color="&H00000000&",
                                      outline=2, shadow=1, alignment=2, margin_v=60, margin_l=50, margin_r=50, spacing=0.5):
    """將 SRT 轉換為 ASS 格式並設置樣式 (字幕生成用)"""
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    try:
        subtitles = list(srt_lib.parse(srt_content))
    except Exception as e:
        print(f"解析 SRT 內容時出錯: {e}")
        print(f"SRT 內容預覽 (前500字):\n{srt_content[:500]}")
        raise

    if language_code == "zh":
        style_name = "Default_Chinese"
        font_name = "Microsoft JhengHe"
        font_size = 104
        actual_margin_l = 100
        actual_margin_r = 100
        actual_margin_v = 100
        actual_spacing = 0
        actual_outline = 3
        actual_shadow = 1.5
        WrapStyle_set =2
    else:
        style_name = "Default_Latin"
        font_name = "Arial"
        font_size = 64
        actual_margin_l = 100
        actual_margin_r = 100
        actual_margin_v = 100
        actual_spacing = 0.5
        actual_outline = 2
        actual_shadow = 1
        WrapStyle_set = 1

    ass_header = f"""[Script Info]
; Script generated by Python script
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
WrapStyle: {WrapStyle_set}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {style_name},{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{back_color},1,0,0,0,100,100,{actual_spacing},0,3,{actual_outline},{actual_shadow},{alignment},{actual_margin_l},{actual_margin_r},{actual_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = ""
    for sub in subtitles:
        start_time_str = step4_5_subgen_format_ass_time(sub.start)
        end_time_str = step4_5_subgen_format_ass_time(sub.end)
        text = sub.content.replace("\n", "\\N")
        events += f"Dialogue: 0,{start_time_str},{end_time_str},{style_name},,0,0,0,,{text}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + events)
    print(f"已將 SRT ({srt_path}) 轉換為 ASS ({ass_path}) 並設置樣式")

def step4_5_subgen_setup_environment(output_dir_subgen):
    """設置字幕生成環境，檢查目錄和 FFmpeg"""
    if not os.path.exists(output_dir_subgen):
        os.makedirs(output_dir_subgen)
        print(f"字幕生成輸出目錄已創建: {output_dir_subgen}")

    if not os.path.isfile(FFMPEG_PATH_SUBGEN):
        print(f"FFmpeg (字幕生成用) 未找到或不是有效文件: {FFMPEG_PATH_SUBGEN}")
        raise FileNotFoundError(f"請確認 FFmpeg (字幕生成用) 路徑: {FFMPEG_PATH_SUBGEN}")
    print(f"FFmpeg (字幕生成用) 路徑已確認: {FFMPEG_PATH_SUBGEN}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        major, minor = torch.cuda.get_device_capability()
        compute_type = "float16" if major >= 7 else "int8"
        if major < 7:
            print(f"GPU compute capability {major}.{minor} < 7.0, 使用 {compute_type} on CUDA.")
        print(f"使用 GPU (字幕生成): {torch.cuda.get_device_name(0)} (CUDA {torch.version.cuda}) (Compute Capability: {major}.{minor})")
    else:
        compute_type = "int8"
        print("未檢測到 GPU (字幕生成)，將使用 CPU 進行 Whisper 轉錄")
    return device, compute_type

def step4_5_subgen_extract_audio(video_path, audio_path):
    """從影片中提取音頻為 WAV 格式 (字幕生成用)"""
    print(f"開始提取音頻 (字幕生成用) 從: {video_path}")
    start_time = time.time()
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"影片檔案未找到 (字幕生成用): {video_path}")
        input_stream = ffmpeg.input(video_path)
        output_stream = ffmpeg.output(input_stream.audio, audio_path, format='wav', acodec='pcm_s16le', ar=24000, ac=1)
        process = ffmpeg.run_async(output_stream, cmd=FFMPEG_PATH_SUBGEN, overwrite_output=True, pipe_stderr=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise ffmpeg.Error('ffmpeg', stdout, stderr)
        print(f"音頻提取完成 (字幕生成用)，耗時: {time.time() - start_time:.2f} 秒，檔案: {audio_path}")
        if stderr:
            print(f"FFmpeg (提取音訊，字幕生成用) 信息:\n{stderr.decode(errors='replace')}")
    except ffmpeg.Error as e:
        error_message = e.stderr.decode(errors='replace') if e.stderr else str(e)
        print(f"提取音頻時 FFmpeg 出錯 (字幕生成用): {error_message}")
        if os.path.exists(audio_path) and os.path.getsize(audio_path) == 0:
            print(f"嘗試刪除可能損壞的音頻檔案: {audio_path}")
            try:
                os.remove(audio_path)
            except OSError as oe:
                print(f"刪除失敗: {oe}")
        raise
    except Exception as e:
        print(f"提取音訊時發生未知錯誤 (字幕生成用): {str(e)}")
        raise

def step4_5_subgen_transcribe_audio(audio_path, model_size, device, compute_type, language_code):
    """轉錄音頻並生成字幕，調整長字幕處理邏輯"""
    print(f"開始載入 Whisper 模型 ({model_size}) 在 {device} (compute_type: {compute_type}) (字幕生成用)...")
    start_time_load = time.time()
    model = None
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"載入 Whisper 模型失敗 (字幕生成用): {e}")
        raise
    print(f"模型載入完成 (字幕生成用)，耗時: {time.time() - start_time_load:.2f} 秒")

    print(f"開始轉錄音頻 ({audio_path}) (目標語言: {language_code}) (字幕生成用)...")
    start_time_transcribe = time.time()
    try:
        if language_code == "zh":
            print(f'使用中文模型並啟用VAD進行分段...')
            segments_generator, info = model.transcribe(
                audio_path,
                language=language_code,
                temperature=0.0,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 450,
                    "speech_pad_ms": 50,
                    "threshold": 0.2
                },
    initial_prompt="請大約4秒到8秒為一個段落。"
            )
        else:
            print(f'use en/es model')
            segments_generator, info = model.transcribe(
                audio_path,
                language=language_code,
                temperature=0.0,
                beam_size=10,
                best_of=5,
                length_penalty=1,
                repetition_penalty=1.0,
                no_repeat_ngram_size=0,
                condition_on_previous_text=True,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 150,
                    "speech_pad_ms": 30,
                    "threshold": 0.2
                },
                hallucination_silence_threshold=1.5,
            )
        print(f"檢測到的音頻語言 (字幕生成用): {info.language} (置信度: {info.language_probability:.2f})")

        subtitles = []
        subtitle_index = 1

        for segment in segments_generator:
            text = segment.text.strip()
            if not text:
                continue

            if language_code == "zh":
                text = step4_5_subgen_convert_to_traditional_chinese(text)

            start_td = timedelta(seconds=segment.start)
            end_td = timedelta(seconds=segment.end)
            subtitles.append(srt_lib.Subtitle(
                index=subtitle_index,
                start=start_td,
                end=end_td,
                content=text
            ))
            subtitle_index += 1

        print(f"音頻轉錄完成 (字幕生成用)，耗時: {time.time() - start_time_transcribe:.2f} 秒")
        print(f"總計生成 {len(subtitles)} 個字幕項目")
        return subtitles
    except Exception as e:
        print(f"轉錄音頻時出錯 (字幕生成用): {str(e)}")
        raise
    finally:
        if model is not None:
            print("DEBUG: Attempting to delete model object.")
            del model
            model = None
            print("DEBUG: Model object deleted.")
        if device == "cuda" and torch.cuda.is_available():
            print("DEBUG: Attempting to empty CUDA cache.")
            torch.cuda.empty_cache()
            print("DEBUG: CUDA cache emptied.")
        print("已釋放 Whisper 模型資源 (字幕生成用)")

def step4_5_subgen_save_srt(subtitles, output_path):
    """將字幕保存為 SRT 檔案 (字幕生成用)"""
    try:
        srt_composed_content = srt_lib.compose(subtitles)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_composed_content)
        print(f"字幕已保存至 (字幕生成用): {output_path}")
    except Exception as e:
        print(f"保存 SRT 字幕時出錯 (字幕生成用): {str(e)}")
        raise

def step4_5_subgen_add_subtitles_to_video(video_path, subtitle_ass_path, output_video_path_target):
    """使用 FFmpeg 將 ASS 字幕嵌入影片，嘗試 CUDA 加速並回退到 CPU (字幕生成用)"""
    print(f"開始嵌入字幕到影片 (字幕生成用): {video_path} 使用字幕: {subtitle_ass_path}")
    start_time = time.time()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"影片檔案未找到 (字幕生成用): {video_path}")
    if not os.path.exists(subtitle_ass_path):
        raise FileNotFoundError(f"ASS 字幕檔案未找到 (字幕生成用): {subtitle_ass_path}")

    escaped_subtitle_path = subtitle_ass_path.replace('\\', '/')
    if os.name == 'nt' and ':' in escaped_subtitle_path:
        drive, tail = os.path.splitdrive(escaped_subtitle_path)
        if drive:
            escaped_subtitle_path = drive.replace(':','\\:') + tail
    
    vf_option = f"subtitles=filename='{escaped_subtitle_path}'"
    print(f"FFmpeg subtitles filter option: {vf_option}")

    encoders_to_try = [
        {"name": "CUDA (h264_nvenc)", "vcodec": "h264_nvenc", "preset": "p2", "params": []},
        {"name": "CPU (libx264 fast)", "vcodec": "libx264", "preset": "fast", "params": []},
        {"name": "CPU (libx264 ultrafast)", "vcodec": "libx264", "preset": "ultrafast", "params": []}
    ]

    success = False
    for enc_info in encoders_to_try:
        print(f"嘗試使用 {enc_info['name']} 進行字幕嵌入 (字幕生成用)...")
        loop_start_time = time.time()
        cmd = [
            FFMPEG_PATH_SUBGEN, "-y",
            "-i", video_path,
            "-vf", vf_option,
            "-c:v", enc_info["vcodec"],
            "-preset", enc_info["preset"],
            "-c:a", "copy",
            *enc_info["params"],
            output_video_path_target
        ]
        print(f"執行 FFmpeg ({enc_info['name']}, 字幕生成用) 命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            print(f"已使用 {enc_info['name']} 生成帶字幕的影片，耗時 (字幕生成用): {time.time() - loop_start_time:.2f} 秒。")
            if result.stderr:
                print(f"FFmpeg ({enc_info['name']}, 字幕生成用) STDERR/INFO:\n{result.stderr}")
            success = True
            break
        except subprocess.CalledProcessError as e:
            print(f"{enc_info['name']} 添加字幕時出錯 (返回碼 {e.returncode}, 字幕生成用):\n標準輸出:\n{e.stdout}\n標準錯誤:\n{e.stderr}")
            if os.path.exists(output_video_path_target):
                try:
                    os.remove(output_video_path_target)
                except OSError:
                    pass
        except Exception as e_generic:
            print(f"使用 {enc_info['name']} 添加字幕過程中發生未知錯誤: {e_generic}")
            if os.path.exists(output_video_path_target):
                try:
                    os.remove(output_video_path_target)
                except OSError:
                    pass
    
    if not success:
        print("所有編碼嘗試均失敗，無法嵌入字幕。")
        raise Exception("FFmpeg embedding failed with all attempted encoders.")
    
    print(f"字幕嵌入影片過程結束 (字幕生成用)。總耗時: {time.time() - start_time:.2f} 秒。輸出檔案: {output_video_path_target}")

# --- 輔助函數 (英文/西班牙文) ---
def en_es_preprocess_text(text: str) -> Tuple[str, str]:
    normalized_space_text = ' '.join(text.split())
    processed_lower_text = normalized_space_text.lower()
    return processed_lower_text, normalized_space_text

def en_es_identify_names(original_case_text_normalized_spaces: str) -> set:
    words = original_case_text_normalized_spaces.split()
    names = set()
    for i, word in enumerate(words):
        if word and word[0].isupper() and len(word) > 1:
            names.add(word)
            if i + 1 < len(words) and words[i+1] and words[i+1][0].isupper():
                names.add(f"{word} {words[i+1]}")
    return names

def en_es_normalize_names(text_lower: str, names_set: set) -> str:
    normalized_text = text_lower
    sorted_names = sorted(list(names_set), key=len, reverse=True)
    for name in sorted_names:
        normalized_text = normalized_text.replace(name.lower(), "<name>")
    return normalized_text

def en_es_parse_srt(srt_path: str) -> List[Tuple[str, str, str]]:
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    srt_blocks = re.split(r'\n\n', srt_content.strip())
    srt_segments = []
    for block in srt_blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_str = lines[1]
            text_str = ' '.join(lines[2:])
            try:
                start_time, end_time = time_str.split(' --> ')
                srt_segments.append((start_time.strip(), end_time.strip(), text_str))
            except ValueError:
                print(f"警告: 解析SRT時間戳失敗，跳過此區塊: {block}")
                continue
    print(f"解析 SRT 檔案 '{srt_path}': 共 {len(srt_segments)} 個段落")
    return srt_segments

def en_es_time_to_ms(time_str: str) -> int:
    """
    將 SRT 時間格式轉換為毫秒。
    """
    try:
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    except Exception as e:
        print(f"時間戳解析失敗：{time_str}，錯誤：{e}")
        return 0

def en_es_write_srt(output_srt_path: str, segments: List[Tuple[str, str, str]]):
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        for i, (start_time, end_time, text) in enumerate(segments, 1):
            f.write(f"{i}\n{start_time} --> {end_time}\n{text.strip()}\n\n")

def en_es_find_best_txt_candidate(
    srt_original_text: str,
    txt_full_normalized_original_case: str,
    txt_current_search_start_idx: int,
    punctuations_for_splitting: Tuple[str, ...] = ('.', '!', '?', ';', ','),
    min_len_ratio: float = 0.6,
    max_len_ratio: float = 2.0,
    absolute_min_chars: int = 15,
    absolute_max_chars: int = 450
) -> Tuple[Optional[str], int, float]:
    if not srt_original_text.strip() or txt_current_search_start_idx >= len(txt_full_normalized_original_case):
        return None, txt_current_search_start_idx, 0.0

    srt_len = len(srt_original_text)
    target_min_candidate_len = max(absolute_min_chars, int(srt_len * min_len_ratio))
    target_max_candidate_len = min(absolute_max_chars, int(srt_len * max_len_ratio))
    target_max_candidate_len = max(target_max_candidate_len, target_min_candidate_len + 20, srt_len + 10)

    best_match_text: Optional[str] = None
    best_match_score: float = -1.0
    best_match_txt_end_idx: int = txt_current_search_start_idx

    srt_processed_low, _ = en_es_preprocess_text(srt_original_text)

    search_window_in_txt = txt_full_normalized_original_case[
        txt_current_search_start_idx : 
        min(len(txt_full_normalized_original_case), txt_current_search_start_idx + target_max_candidate_len + 50)
    ]

    if not search_window_in_txt:
        return None, txt_current_search_start_idx, 0.0

    possible_end_points = set()
    for i, char in enumerate(search_window_in_txt):
        if char in punctuations_for_splitting and (i + 1 < len(search_window_in_txt) and search_window_in_txt[i + 1] == ' '):
            possible_end_points.add(i + 2)  # 標點符號後的空格
        elif char == ' ' and i >= target_min_candidate_len:
            possible_end_points.add(i + 1)  # 單詞間的空格
    
    step = max(10, int(srt_len * 0.1))
    for i in range(target_min_candidate_len, len(search_window_in_txt) + 1, step):
        possible_end_points.add(i)
    possible_end_points.add(len(search_window_in_txt))

    sorted_end_points = sorted(list(p for p in possible_end_points if p >= target_min_candidate_len and p <= target_max_candidate_len + 5))

    if not sorted_end_points and len(search_window_in_txt) >= absolute_min_chars:
        sorted_end_points.append(min(len(search_window_in_txt), max(absolute_min_chars, srt_len)))

    for end_offset in sorted_end_points:
        if end_offset == 0: continue
        
        candidate_txt_original = search_window_in_txt[:end_offset].strip()
        if not candidate_txt_original:
            continue

        text_for_local_names = srt_original_text + " " + candidate_txt_original
        locally_identified_names = en_es_identify_names(text_for_local_names)
        srt_normalized_comp = en_es_normalize_names(srt_processed_low, locally_identified_names)
        txt_cand_processed_low, _ = en_es_preprocess_text(candidate_txt_original)
        txt_cand_normalized_comp = en_es_normalize_names(txt_cand_processed_low, locally_identified_names)

        current_score = 0.0
        if srt_normalized_comp.strip() or txt_cand_normalized_comp.strip():
            matcher = difflib.SequenceMatcher(None, srt_normalized_comp, txt_cand_normalized_comp)
            current_score = matcher.ratio()
        elif not srt_normalized_comp.strip() and not txt_cand_normalized_comp.strip():
            current_score = 1.0

        len_penalty = 0
        len_s = len(srt_normalized_comp)
        len_t = len(txt_cand_normalized_comp)
        if len_s > 0 and len_t > 0:
            ratio_len = min(len_s, len_t) / max(len_s, len_t)
            len_penalty = (1.0 - ratio_len) * 0.05
        
        adjusted_score = current_score - len_penalty

        if adjusted_score > best_match_score:
            best_match_score = adjusted_score
            best_match_text = candidate_txt_original
            best_match_txt_end_idx = txt_current_search_start_idx + end_offset
    
    return best_match_text, best_match_txt_end_idx, best_match_score

def en_es_correct_srt_by_flexible_matching(
    merged_srt_segments_input: List[Tuple[str, str, str]],
    full_txt_content: str,
    similarity_score_threshold: float = 0.5  # 提高閾值到 0.5
) -> List[Tuple[str, str, str]]:
    final_corrected_segments = []
    _txt_lower_processed_full, txt_original_case_normalized_spaces_full = en_es_preprocess_text(full_txt_content)
    current_txt_char_pointer = 0

    for idx, (srt_seg_start_time, srt_seg_end_time, srt_original_seg_text_merged) in enumerate(merged_srt_segments_input):
        if not srt_original_seg_text_merged.strip():
            final_corrected_segments.append((srt_seg_start_time, srt_seg_end_time, srt_original_seg_text_merged.strip()))
            continue
        
        if current_txt_char_pointer >= len(txt_original_case_normalized_spaces_full):
            final_corrected_segments.append((srt_seg_start_time, srt_seg_end_time, srt_original_seg_text_merged.strip()))
            continue

        best_txt_match_text, txt_match_ends_at_char_idx, match_score = en_es_find_best_txt_candidate(
            srt_original_seg_text_merged,
            txt_original_case_normalized_spaces_full,
            current_txt_char_pointer
        )
        
        text_to_use_for_srt = srt_original_seg_text_merged

        if best_txt_match_text is not None and match_score > similarity_score_threshold:
            text_to_use_for_srt = best_txt_match_text
            current_txt_char_pointer = txt_match_ends_at_char_idx
        else:
            if best_txt_match_text is not None:
                current_txt_char_pointer = txt_match_ends_at_char_idx
            else:
                advance_chars = max(5, len(srt_original_seg_text_merged)//2)
                current_txt_char_pointer = min(current_txt_char_pointer + advance_chars, len(txt_original_case_normalized_spaces_full))

        final_corrected_segments.append((srt_seg_start_time, srt_seg_end_time, text_to_use_for_srt.strip()))
            
    return final_corrected_segments

# --- 輔助函數 (中文) ---
def ZH_preprocess_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def ZH_tokenize_for_comparison(text: str) -> str:
    return ' '.join(jieba.cut(text, cut_all=False))

def ZH_parse_srt(srt_path: str) -> List[Tuple[str, str, str]]:
    if not os.path.exists(srt_path):
        print(f"SRT 檔案 '{srt_path}' 不存在")
        return []
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    except Exception as e:
        print(f"讀取 SRT 檔案 '{srt_path}' 失敗: {e}")
        return []
    
    srt_blocks = re.split(r'\n\n', srt_content.strip())
    srt_segments = []
    for block in srt_blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_str = lines[1]
            text_str = ZH_preprocess_text(' '.join(lines[2:]))
            try:
                start_time, end_time = time_str.split(' --> ')
                srt_segments.append((start_time.strip(), end_time.strip(), text_str))
            except ValueError:
                print(f"解析SRT時間戳失敗，跳過此區塊: {block}")
                continue
    print(f"解析 SRT 檔案 '{srt_path}': 共 {len(srt_segments)} 個段落")
    return srt_segments

def ZH_time_to_ms(time_str: str) -> int:
    try:
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    except Exception:
        return 0

def ZH_write_srt(output_srt_path: str, segments: List[Tuple[str, str, str]]):
    try:
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            for i, (start_time, end_time, text) in enumerate(segments, 1):
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        print(f"成功寫入 SRT 檔案: {output_srt_path}")
    except Exception as e:
        print(f"寫入 SRT 檔案 '{output_srt_path}' 失敗: {e}")

def ZH_find_best_txt_candidate(
    srt_original_text: str,
    txt_full_original: str,
    txt_current_search_start_idx: int,
    punctuations_for_splitting: Tuple[str, ...] = ('。', '！', '？', '，', '；', '：', ',', '?', '!'),
    min_len_ratio: float = 0.5,  # 提高到 0.5
    max_len_ratio: float = 2.0,  # 降低到 2.0
    absolute_min_chars: int = 5,  # 至少 5 字元
    absolute_max_chars: int = 200  # 限制最大長度
) -> Tuple[Optional[str], int, float]:
    
    if not srt_original_text.strip() or txt_current_search_start_idx >= len(txt_full_original):
        return None, txt_current_search_start_idx, 0.0

    srt_len = len(srt_original_text)
    target_min_candidate_len = max(absolute_min_chars, int(srt_len * min_len_ratio))
    target_max_candidate_len = min(absolute_max_chars, int(srt_len * max_len_ratio))
    target_max_candidate_len = max(target_max_candidate_len, target_min_candidate_len + 20, srt_len + 10)

    best_match_text: Optional[str] = None
    best_match_score: float = -1.0
    best_match_txt_end_idx: int = txt_current_search_start_idx

    search_window_original = txt_full_original[
        txt_current_search_start_idx : 
        min(len(txt_full_original), txt_current_search_start_idx + target_max_candidate_len + 100)
    ]

    if not search_window_original:
        return None, txt_current_search_start_idx, 0.0

    srt_for_comparison = ZH_tokenize_for_comparison(srt_original_text)
    
    possible_end_points = set()
    for i, char in enumerate(search_window_original):
        if char in punctuations_for_splitting:
            possible_end_points.add(i + 1)
    step = max(5, int(srt_len * 0.1))
    for i in range(target_min_candidate_len, len(search_window_original) + 1, step):
        possible_end_points.add(i)
    possible_end_points.add(len(search_window_original))
    sorted_end_points = sorted(list(p for p in possible_end_points if p >= target_min_candidate_len))

    for end_offset in sorted_end_points:
        if end_offset == 0: continue
        
        candidate_txt_original = search_window_original[:end_offset]
        if not candidate_txt_original.strip(): continue
        txt_cand_for_comparison = ZH_tokenize_for_comparison(candidate_txt_original)

        matcher = difflib.SequenceMatcher(None, srt_for_comparison, txt_cand_for_comparison, autojunk=False)
        current_score = matcher.ratio()

        len_penalty = 0
        len_s_comp = len(srt_for_comparison)
        len_t_comp = len(txt_cand_for_comparison)
        if len_s_comp > 0 and len_t_comp > 0:
            ratio_len = min(len_s_comp, len_t_comp) / max(len_s_comp, len_t_comp)
            len_penalty = (1.0 - ratio_len) * 0.05
        
        adjusted_score = current_score - len_penalty

        if adjusted_score > best_match_score:
            best_match_score = adjusted_score
            best_match_text = candidate_txt_original
            best_match_txt_end_idx = txt_current_search_start_idx + end_offset
    
    return best_match_text, best_match_txt_end_idx, best_match_score

def ZH_correct_srt_by_flexible_matching(
    merged_srt_segments_input: List[Tuple[str, str, str]],
    full_txt_content: str,
    similarity_score_threshold: float = 0.5  # 提高閾值到 0.5
) -> List[Tuple[str, str, str]]:
    
    final_corrected_segments = []
    txt_original_full = ZH_preprocess_text(full_txt_content)
    current_txt_char_pointer = 0
    used_text = ""  # 記錄已使用的 TXT 文本

    for idx, (srt_seg_start_time, srt_seg_end_time, srt_original_seg_text_merged) in enumerate(merged_srt_segments_input):
        log_msg_prefix = f"--- 段落 {idx + 1} | SRT: '{srt_original_seg_text_merged[:40]}...'"
        
        if not srt_original_seg_text_merged.strip():
            final_corrected_segments.append((srt_seg_start_time, srt_seg_end_time, ""))
            continue
        
        # 使用 NER 判斷是否為人名
        is_name = False
        if nlp:
            doc = nlp(srt_original_seg_text_merged)
            is_name = any(ent.label_ == "PERSON" for ent in doc.ents)
        
        # 根據是否為人名設置不同的相似度閾值
        local_threshold = similarity_score_threshold
        if is_name:
            local_threshold = 0.01  # 人名使用更高閾值
            print(f"{log_msg_prefix} -> 識別為人名，設置相似度閾值為 {local_threshold}")
        else:
            print(f"{log_msg_prefix} -> 非人名，保持相似度閾值為 {local_threshold}")

        # 尋找最佳匹配
        best_txt_match_text, txt_match_ends_at_char_idx, match_score = ZH_find_best_txt_candidate(
            srt_original_seg_text_merged,
            txt_original_full,
            current_txt_char_pointer
        )
        
        text_to_use_for_srt = srt_original_seg_text_merged

        if best_txt_match_text is not None and match_score > local_threshold:
            # 檢查是否重複前段文字
            if best_txt_match_text in used_text[-50:]:  # 檢查最後 50 字元
                print(f"{log_msg_prefix} -> 候選包含前段文字，保留 SRT 原文")
                text_to_use_for_srt = srt_original_seg_text_merged
            else:
                text_to_use_for_srt = ZH_preprocess_text(best_txt_match_text)
                current_txt_char_pointer = txt_match_ends_at_char_idx
                used_text += text_to_use_for_srt
                print(f"{log_msg_prefix} -> 匹配成功 (分數 {match_score:.3f})，替換為 TXT: '{text_to_use_for_srt[:40]}...' | 指針 -> {current_txt_char_pointer}")
        else:
            if best_txt_match_text is not None:
                current_txt_char_pointer = txt_match_ends_at_char_idx
                print(f"{log_msg_prefix} -> 匹配失敗 (分數 {match_score:.3f} 未達閾值 {local_threshold})，保留原文，指針推進至 {current_txt_char_pointer}")
            else:
                advance_chars = max(10, len(srt_original_seg_text_merged))
                current_txt_char_pointer = min(current_txt_char_pointer + advance_chars, len(txt_original_full))
                print(f"{log_msg_prefix} -> 未找到匹配，保留原文，指針推進至 {current_txt_char_pointer}")

        final_corrected_segments.append((srt_seg_start_time, srt_seg_end_time, text_to_use_for_srt))
            
    return final_corrected_segments

from datetime import timedelta

def save_srt_segments_to_txt(segments: List[Tuple[str, str, str]], output_path: str) -> None:
    """
    將 SRT 段落保存到 TXT 檔案，每段包含開始時間、結束時間和文本，並以空行分隔。
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, (start_time, end_time, text) in enumerate(segments, 1):
                f.write(f"段落 {i}:\n")
                f.write(f"開始時間: {start_time}\n")
                f.write(f"結束時間: {end_time}\n")
                f.write(f"文本: {text}\n")
                f.write("\n")
        print(f"已將 {len(segments)} 個段落保存至: {output_path}")
    except Exception as e:
        print(f"保存 TXT 檔案到 {output_path} 失敗: {e}")


def ZH_final_is_chinese_char(char):
    """判斷是否為中文字元（不包括標點符號）"""
    return '\u4e00' <= char <= '\u9fff'

def ZH_final_is_punctuation(char):
    """判斷是否為標點符號"""
    punctuations = '。！？「」()【】，；：、“”‘’.,;:!?"\' '
    return char in punctuations

def ZH_final_time_to_seconds(time_str):
    """將 SRT 時間格式轉換為秒"""
    h, m, s = time_str.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def ZH_final_seconds_to_time(seconds):
    """將秒轉換為 SRT 時間格式"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

def ZH_final_calculate_width(text):
    """計算文本的字幅，忽略首尾標點符號及指定的符號"""
    ignored_symbols = set('「」【】()[]')  # 定義需要忽略的符號
    text = text.strip()
    while text and ZH_final_is_punctuation(text[0]):
        text = text[1:]
    if not text:
        return 0
    width = 0
    i = 0
    punctuation_widths = {
        '。': 2.0,  # 句號，較長停頓
        '！': 2.0,  # 感嘆號
        '？': 2.0,  # 問號
        '，': 1.5,  # 逗號，較短停頓
        '；': 1.5,  # 分號
        '：': 1.5,  # 冒號
        '、': 1.5,  # 頓號
        # 其他標點符號默認為 1.0
    }
    while i < len(text):
        if text[i] in ignored_symbols:
            i += 1
            continue
        elif ZH_final_is_chinese_char(text[i]):
            width += 1
            i += 1
        elif ZH_final_is_punctuation(text[i]):
            j = i
            # 累積連續的標點符號
            while j < len(text) and ZH_final_is_punctuation(text[j]):
                if text[j] not in ignored_symbols:
                    # 逐字查詢寬度並累加
                    width += punctuation_widths.get(text[j], 1) # 預設值可設為0.5或1.0
                j += 1
            i = j # 直接跳到標點符號的結尾
        else:
            i += 1
    return width
def ZH_final_parse_srt(srt_content):
    """解析 SRT 內容為段落列表"""
    segments = []
    for block in re.split(r'\n\n', srt_content.strip()):
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            index = int(lines[0])
            start, end = lines[1].split(' --> ')
            text = '\n'.join(lines[2:])
            segments.append({'index': index, 'start': start, 'end': end, 'text': text})
    return segments

def ZH_final_add_smart_newlines(text):
    """在每個標點符號後插入 \\N，處理連續標點符號"""
    result = []
    i = 0
    while i < len(text):
        if ZH_final_is_punctuation(text[i]):
            j = i
            while j < len(text) and ZH_final_is_punctuation(text[j]):
                j += 1
            result.append(text[i:j])
            result.append('\\N')
            i = j
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)

def ZH_final_add_spaces_to_srt(srt_input_path, srt_output_path):
    try:
        with open(srt_input_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        segments = ZH_final_parse_srt(srt_content)
        
        new_segments = []
        for segment in segments:
            GAP_ADJUSTMENT = 0.2 # 單位：秒。您可以調整這個值，例如 0.2, 0.5
            original_start = ZH_final_time_to_seconds(segment['start'])
            original_end = ZH_final_time_to_seconds(segment['end'])
            text_with_newlines = ZH_final_add_smart_newlines(segment['text'])
            sub_texts = [t.strip() for t in text_with_newlines.split('\\N') if t.strip()]
            if not sub_texts:
                new_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
                continue
            sub_widths = [ZH_final_calculate_width(sub_text) for sub_text in sub_texts]
            total_width = sum(sub_widths)
            if total_width == 0:
                new_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
                continue
            total_duration = original_end - original_start
            effective_duration = total_duration - (2 * GAP_ADJUSTMENT)

            # 如果有效時長小於0，則不進行調整，避免錯誤
            if effective_duration <= 0:
                effective_duration = total_duration
                current_time = original_start
            else:
                # 2. 將計算的起始時間向後推
                current_time = original_start + GAP_ADJUSTMENT

            for i, sub_text in enumerate(sub_texts):
                sub_width = sub_widths[i]
                if i < len(sub_texts) - 1:
                    # 3. 根據有效的時長來按比例計算子段落時長
                    sub_duration = (sub_width / total_width) * effective_duration
                    sub_end_time = min(current_time + sub_duration, original_end)
                else:
                    sub_end_time = original_end  # 最後一個子段落對齊原始結束時間，這很重要

                new_segments.append({
                    'start': ZH_final_seconds_to_time(current_time),
                    'end': ZH_final_seconds_to_time(sub_end_time),
                    'text': sub_text
                })
                if i < len(sub_texts) - 1:
                    current_time = sub_end_time
        with open(srt_output_path, 'w', encoding='utf-8') as f:
            for idx, seg in enumerate(new_segments, start=1):
                f.write(f"{idx}\n{seg['start']} --> {seg['end']}\n{seg['text']}\n\n")
        print(f"已處理 SRT 文件並智能添加換行符及分段，保存至: {srt_output_path}")
    except Exception as e:
        print(f"處理 SRT 文件時出錯: {e}")

def ZH_final_remove_punctuations_from_srt(input_path, output_path):
    """
    讀取 SRT 文件，移除每個段落文本中的標點符號，並保存到新文件。
    
    參數:
        input_path (str): 輸入的 SRT 文件路徑
        output_path (str): 輸出的 SRT 文件路徑
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # 分割 SRT 文件為單獨的段落
        srt_blocks = re.split(r'\n\n', srt_content.strip())
        processed_blocks = []
        
        for block in srt_blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:  # 確保是有效的 SRT 段落
                index = lines[0]  # 段落編號
                timestamp = lines[1]  # 時間戳
                text_lines = lines[2:]  # 文本內容
                # 合併多行文本並移除標點符號
                text = ''.join(text_lines)
                # 定義要移除的標點符號（中文和英文）
                punctuations = r'[。！？「」()【】，；：、“”‘’.,;:!?"\' ]'
                # 移除標點符號
                text_no_punct = re.sub(punctuations, '', text)
                # 重新組裝段落
                processed_block = f"{index}\n{timestamp}\n{text_no_punct}"
                processed_blocks.append(processed_block)
            else:
                processed_blocks.append(block)  # 無效段落保持不變
        
        # 將處理後的內容寫入新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(processed_blocks))
        print(f"已移除標點符號並保存至: {output_path}")
    except Exception as e:
        print(f"移除標點符號時出錯: {e}")

def ZH_merge_srt_segments(segments: List[Tuple[str, str, str]], max_gap_ms: int = 500) -> List[Tuple[str, str, str]]:
    """
    合併時間間隔很近的 SRT 片段，形成更長的句子。
    """
    if not segments:
        return []

    merged_segments = []
    current_start, _, current_text = segments[0]
    current_end = segments[0][1]

    for i in range(1, len(segments)):
        next_start_str, next_end_str, next_text = segments[i]
        
        # 計算時間差
        gap = ZH_time_to_ms(next_start_str) - ZH_time_to_ms(current_end)

        if gap <= max_gap_ms and len(current_text) < 100: # 如果間隔小於閾值，且當前句子不太長，就合併
            current_text += " " + next_text.strip() # 合併文本
            current_end = next_end_str # 更新結束時間
        else:
            # 間隔太大或句子太長，保存當前段落，開始新段落
            merged_segments.append((current_start, current_end, current_text.strip()))
            current_start, current_end, current_text = segments[i]

    # 不要忘記保存最後一個段落
    merged_segments.append((current_start, current_end, current_text.strip()))
    
    print(f"原始SRT片段數量: {len(segments)}, 合併後片段數量: {len(merged_segments)}")
    return merged_segments
def EN_merge_srt_segments(segments: List[Tuple[str, str, str]], max_duration_ms: int = 7000) -> List[Tuple[str, str, str]]:
    """
    合併 SRT 片段，僅根據段落時間長短進行合併，確保每段至少 7 秒。

    邏輯：
    1. 檢查當前段落的持續時間，若小於 7000ms，合併下一段。
    2. 合併後檢查總持續時間，若仍小於 7000ms，繼續合併，直到滿足條件或無下一段。
    3. 若合併後超過 7000ms，保存合併結果。

    參數:
        segments: List[Tuple[str, str, str]] - 包含 (start_time, end_time, text) 的 SRT 段落
        max_duration_ms: int - 最小持續時間（毫秒），預設為 7000ms（7秒）

    返回:
        List[Tuple[str, str, str]] - 合併後的 SRT 段落
    """
    if not segments:
        print("輸入的 SRT 段落為空，無法合併。")
        return []

    merged_segments = []
    current_start, current_end, current_text = segments[0]

    print(f"開始合併 SRT 片段，總段落數：{len(segments)}")

    i = 1
    while i < len(segments):
        next_start_str, next_end_str, next_text = segments[i]
        
        # 計算當前段落的持續時間
        current_duration = en_es_time_to_ms(current_end) - en_es_time_to_ms(current_start)
        print(f"段落 {i}: 持續時間 = {current_duration}ms，當前文本 = '{current_text[:50]}...'，下段文本 = '{next_text[:50]}...'")

        # 如果當前段落持續時間小於 7000ms，嘗試合併下一段
        if current_duration < max_duration_ms:
            print(f"合併段落 {i}，因為持續時間 {current_duration}ms < {max_duration_ms}ms")
            current_text += " " + next_text.strip()
            current_end = next_end_str
            i += 1
            continue

        # 如果當前段落持續時間 >= 7000ms，保存當前段落
        print(f"不合併段落 {i}，保存當前段落：'{current_text[:50]}...'，持續時間 = {current_duration}ms")
        merged_segments.append((current_start, current_end, current_text.strip()))
        current_start, current_end, current_text = segments[i]
        i += 1

    # 保存最後一個段落
    current_duration = en_es_time_to_ms(current_end) - en_es_time_to_ms(current_start)
    print(f"保存最後段落：'{current_text[:50]}...'，持續時間 = {current_duration}ms")
    merged_segments.append((current_start, current_end, current_text.strip()))
    
    print(f"原始 SRT 片段數量: {len(segments)}, 合併後片段數量: {len(merged_segments)}")
    return merged_segments


def EN_final_time_to_seconds(time_str):
    """將 SRT 時間格式轉換為秒"""
    h, m, s = time_str.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def EN_final_seconds_to_time(seconds):
    """將秒轉換為 SRT 時間格式"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

def EN_final_calculate_width(text):
    """計算文本的字幅（字符數，包括空格和標點）"""
    return len(text.strip())

def EN_final_parse_srt(srt_content):
    """解析 SRT 內容為段落列表"""
    segments = []
    for block in re.split(r'\n\n', srt_content.strip()):
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            index = int(lines[0])
            start, end = lines[1].split(' --> ')
            text = '\n'.join(lines[2:])
            segments.append({'index': index, 'start': start, 'end': end, 'text': text})
    return segments

def EN_final_add_newlines_to_srt(srt_input_path, srt_output_path):
    """處理英文 SRT 文件，按句號分段並調整時間戳"""
    try:
        with open(srt_input_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        segments = EN_final_parse_srt(srt_content)
        
        new_segments = []
        i = 0
        while i < len(segments):
            # 合併段落直到完整句子
            combined_text = segments[i]['text']
            combined_start = EN_final_time_to_seconds(segments[i]['start'])
            combined_end = EN_final_time_to_seconds(segments[i]['end'])
            j = i + 1
            while (j < len(segments) and 
                   ('.' not in combined_text or 
                    (j < len(segments) and not segments[j]['text'][0].isupper()))):
                combined_text += ' ' + segments[j]['text']
                combined_end = EN_final_time_to_seconds(segments[j]['end'])
                j += 1
            
            # 按句號分段，保留句號
            sub_texts = []
            current_sentence = ""
            for char in combined_text:
                current_sentence += char
                if char == '.':
                    sub_texts.append(current_sentence.strip())
                    current_sentence = ""
            if current_sentence.strip():
                sub_texts.append(current_sentence.strip())
            
            if not sub_texts:
                new_segments.append({
                    'start': segments[i]['start'],
                    'end': segments[i]['end'],
                    'text': segments[i]['text']
                })
                i += 1
                continue
            
            # 計算字幅和時間分配
            sub_widths = [EN_final_calculate_width(sub_text) for sub_text in sub_texts]
            total_width = sum(sub_widths)
            if total_width == 0:
                new_segments.append({
                    'start': segments[i]['start'],
                    'end': segments[i]['end'],
                    'text': segments[i]['text']
                })
                i += 1
                continue
            
            total_duration = combined_end - combined_start
            current_time = combined_start
            for k, sub_text in enumerate(sub_texts):
                sub_width = sub_widths[k]
                if k < len(sub_texts) - 1:
                    sub_duration = (sub_width / total_width) * total_duration
                    sub_end_time = current_time + sub_duration
                else:
                    sub_end_time = combined_end  # 最後一個子段落對齊原始結束時間
                new_segments.append({
                    'start': EN_final_seconds_to_time(current_time),
                    'end': EN_final_seconds_to_time(sub_end_time),
                    'text': sub_text
                })
                if k < len(sub_texts) - 1:
                    current_time = sub_end_time
            
            i = j
        
        with open(srt_output_path, 'w', encoding='utf-8') as f:
            for idx, seg in enumerate(new_segments, start=1):
                f.write(f"{idx}\n{seg['start']} --> {seg['end']}\n{seg['text']}\n\n")
        print(f"已處理英文 SRT 文件並按句號分段，保存至: {srt_output_path}")
    except Exception as e:
        print(f"處理英文 SRT 文件時出錯: {e}")

# --- 主流程函式 ---
def step4_5_generate_subtitles_and_embed(story_folder_param):
    """為 '故事影片_mp4' 目錄中的所有 MP4 文件生成並嵌入字幕"""
    mp4_video_dir = os.path.join(story_folder_param, "故事影片_mp4")
    if not os.path.isdir(mp4_video_dir):
        print(f"影片目錄不存在或不是一個目錄: {mp4_video_dir}")
        return

    print(f"開始處理目錄中的影片: {mp4_video_dir}")
    video_files = [f for f in os.listdir(mp4_video_dir) if f.lower().endswith(".mp4")]
    if not video_files:
        print(f"在 {mp4_video_dir} 中未找到 .mp4 檔案。")
        return

    for mp4_filename_item in video_files:
        video_file_to_subtitle = os.path.join(mp4_video_dir, mp4_filename_item)
        print(f"\n--- 開始 Step 4.5: 為影片添加字幕: {video_file_to_subtitle} ---")
        
        base_video_filename = os.path.splitext(mp4_filename_item)[0]
        sub_output_dir = os.path.join(mp4_video_dir, f"{base_video_filename}_subgen_temp")
        
        parts = base_video_filename.rsplit("_", 2)
        if len(parts) >= 3:
            story_name_parts = parts[:-2]
            story_name = "_".join(story_name_parts) if isinstance(story_name_parts, list) and len(story_name_parts) > 1 else (story_name_parts[0] if isinstance(story_name_parts, list) and story_name_parts else "")
            language = parts[-2]
            voice = parts[-1]
            language_code = language_mapping.get(language)
            if not language_code:
                print(f"未知語言: {language} 在檔案 {base_video_filename}")
                continue
            if not story_name:
                print(f"無法從檔案名中解析出故事名稱: {base_video_filename}")
                continue
        else:
            print(f"警告: 檔案名稱格式無法解析語言或故事名稱 '{mp4_filename_item}'。跳過此檔案。")
            print("預期格式: StoryName_語言_聲音.mp4 (例如: MyStory_英文_Female1.mp4)")
            continue

        audio_path = os.path.join(sub_output_dir, f"{base_video_filename}_audio.wav")
        srt_path = os.path.join(sub_output_dir, f"{base_video_filename}_subtitles.srt")
        ass_path = os.path.join(sub_output_dir, f"{base_video_filename}_subtitles.ass")
        temp_output_video_path = os.path.join(sub_output_dir, f"{base_video_filename}_with_subs_temp.mp4")

        original_text_filename = f"{story_name}_full_{language}_{voice}.txt"
        original_text_path = os.path.join(story_folder_param, "總篇章_各語言", original_text_filename)

        try:
            device_subgen, compute_type_subgen = step4_5_subgen_setup_environment(sub_output_dir)
            step4_5_subgen_extract_audio(video_file_to_subtitle, audio_path)
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                print(f"錯誤：音訊檔案 {audio_path} 未成功提取或為空。跳過字幕轉錄。")
                continue
            
            raw_whisper_subtitles = step4_5_subgen_transcribe_audio(
                audio_path,
                WHISPER_MODEL_SIZE,
                device_subgen,
                compute_type_subgen,
                language_code
            )
            if not raw_whisper_subtitles:
                print("Whisper 未能生成有效字幕內容。跳過後續步驟。")
                continue

            if language_code == "zh" and os.path.exists(original_text_path):
                print(f"讀取 TXT 檔案: {original_text_path}")
                with open(original_text_path, 'r', encoding='utf-8') as f:
                    txt_content = f.read()
                
                orginal_srt_for_parsing_path = os.path.join(sub_output_dir, "temp_for_original.srt")
                temp_srt_for_parsing_path = os.path.join(sub_output_dir, "temp_for_parse.txt")
                step4_5_subgen_save_srt(raw_whisper_subtitles, orginal_srt_for_parsing_path)

                subtitles_object = ZH_parse_srt(orginal_srt_for_parsing_path)
                # --- 新增的合併步驟 ---
                print("檢測到Whisper輸出較為零碎，開始合併SRT片段...")
                merged_subtitles_object = ZH_merge_srt_segments(subtitles_object, max_gap_ms=5000) # 間隔小於0.3秒就合併
                # ----------------------
                save_srt_segments_to_txt(merged_subtitles_object, temp_srt_for_parsing_path)
                
                print("已使用 VAD 進行分段，跳過手動合併步驟，直接進行文本校正。")
                
                truly_corrected_segments = ZH_correct_srt_by_flexible_matching(
                    merged_subtitles_object,
                    txt_content,
                    similarity_score_threshold=0.5  # 提高到 0.5
                )
                
                ZH_write_srt(srt_path, truly_corrected_segments)
                
                # 定義處理後的 SRT 文件路徑
                processed_srt_path = os.path.join(sub_output_dir, f"{base_video_filename}_subtitles_processed.srt")
                final_srt_path = os.path.join(sub_output_dir, f"{base_video_filename}_subtitles_final.srt")
                # 處理 SRT 文件，在每個字符前後添加空格
                ZH_final_add_spaces_to_srt(srt_path, processed_srt_path)

                ZH_final_remove_punctuations_from_srt(processed_srt_path,final_srt_path)

                print(f"已保存最終 SRT: {final_srt_path}")

                step4_5_subgen_convert_srt_to_ass(final_srt_path, ass_path, PREFERRED_FONT_SUBGEN, 0, language_code)
                

            
            elif os.path.exists(original_text_path):  # 處理英文/西班牙文
                print(f"讀取 TXT 檔案: {original_text_path}")
                with open(original_text_path, 'r', encoding='utf-8') as f:
                    txt_content = f.read()
                orginal_srt_for_parsing_path = os.path.join(sub_output_dir, "temp_for_original.srt")
                
                temp_srt_for_parsing_path = os.path.join(sub_output_dir, "temp_for_parse.txt")
                step4_5_subgen_save_srt(raw_whisper_subtitles, orginal_srt_for_parsing_path)

                raw_srt_segments = en_es_parse_srt(orginal_srt_for_parsing_path)
                # --- 新增的合併步驟 ---
                print("檢測到Whisper輸出較為零碎，開始合併SRT片段...")
                merged_srt_segments = EN_merge_srt_segments(raw_srt_segments, max_duration_ms=4000)
                # ----------------------
                save_srt_segments_to_txt(merged_srt_segments, temp_srt_for_parsing_path)
                
                print("已使用 VAD 進行分段，跳過額外手動合併步驟，直接進行文本校正。")
                print(f"開始校正 {len(merged_srt_segments)} 個合併後 SRT 段落...")

                truly_corrected_segments = en_es_correct_srt_by_flexible_matching(
                    merged_srt_segments,
                    txt_content,
                    similarity_score_threshold=0.5
                )
                
                en_es_write_srt(srt_path, truly_corrected_segments)
                print(f"校正完成。最終結果已儲存到: {srt_path}")
                
                # 直接使用校正後的 SRT 文件進行 ASS 轉換，移除 EN_final_add_newlines_to_srt 步驟
                step4_5_subgen_convert_srt_to_ass(srt_path, ass_path, PREFERRED_FONT_SUBGEN, 0, language_code)


            else:
                print(f"TXT 檔案 {original_text_path} 不存在，無法進行校正，直接使用 Whisper 結果。")
                step4_5_subgen_save_srt(raw_whisper_subtitles, srt_path)


            if not os.path.exists(ass_path) or os.path.getsize(ass_path) == 0:
                print(f"錯誤：ASS 字幕檔案 {ass_path} 未成功生成或為空。跳過字幕嵌入。")
                continue

            step4_5_subgen_add_subtitles_to_video(video_file_to_subtitle, ass_path, temp_output_video_path)

            if os.path.exists(temp_output_video_path) and os.path.getsize(temp_output_video_path) > 0:
                target_video_path = video_file_to_subtitle
                print(f"準備將帶字幕的影片 {temp_output_video_path} 移至 {target_video_path}")
                try:
                    shutil.move(temp_output_video_path, target_video_path)
                    print(f"字幕嵌入成功，已將臨時影片移動並覆蓋原影片: {target_video_path}")
                except Exception as e_move:
                    print(f"移動/覆蓋影片失敗 {temp_output_video_path} -> {target_video_path}: {e_move}")
                    print("將嘗試複製...")
                    try:
                        shutil.copy2(temp_output_video_path, target_video_path)
                        os.remove(temp_output_video_path)
                        print(f"字幕嵌入成功 (通過複製)，已覆蓋原影片: {target_video_path}")
                    except Exception as e_copy:
                        print(f"複製/覆蓋影片也失敗: {e_copy}。帶字幕的影片保留在: {temp_output_video_path}")
            else:
                print(f"錯誤: 字幕嵌入後的影片 {temp_output_video_path} 未生成或為空。原影片未被修改。")

            print(f"--- Step 4.5 完成: 影片 {mp4_filename_item} 的字幕處理流程結束 ---")

        except FileNotFoundError as e_fnf:
            print(f"檔案錯誤 (影片 {mp4_filename_item} 的字幕生成步驟): {e_fnf}")
        except ffmpeg.Error as e_ff:
            error_detail = e_ff.stderr.decode(errors='replace') if e_ff.stderr else str(e_ff)
            print(f"FFmpeg 相關操作失敗 (影片 {mp4_filename_item} 的字幕生成步驟): {error_detail}")
        except Exception as e_subgen:
            print(f"影片 {mp4_filename_item} 的字幕生成步驟中發生了未預料的錯誤: {e_subgen}")
            import traceback
            traceback.print_exc()

    print("\n--- 所有影片處理完畢 ---")

        


# Step 5: 生成 YouTube 封面
language_map = {"繁體中文": "", "英文": "en", "西班牙語": "es"}
fonts = {
    "繁體中文": "C:\\Windows\\Fonts\\msjhbd.ttc",
    "英文": "C:\\Windows\\Fonts\\arialbd.ttf",
    "西班牙語": "C:\\Windows\\Fonts\\arialbd.ttf"
}

step5_effects = {
    "彩色漸層": {"gradient": True, "stroke": True, "shadow": True, "glow": True}
}

def step5_get_rainbow_gradient(y, height):
    segment = height / 5
    y = y % height
    if y < segment:
        r, g, b = 255, int(165 * (y / segment)), 0
    elif y < 2 * segment:
        r, g, b = 255, 165 + int(90 * ((y - segment) / segment)), 0
    elif y < 3 * segment:
        r, g, b = int(255 * (1 - (y - 2 * segment) / segment)), 255, 0
    elif y < 4 * segment:
        r, g, b = 0, 255, int(255 * ((y - 3 * segment) / segment))
    else:
        r, g, b = 0, int(255 * (1 - (y - 4 * segment) / segment)), 255
    return (r, g, b)

def step5_adjust_text(draw, text, font_path, initial_font_size, max_width, max_height, position, lang, line_spacing):
    font_size = initial_font_size
    font = ImageFont.truetype(font_path, font_size)

    def wrap_text(text, font, max_width, lang):
        if lang in ["英文", "德語", "法語", "西班牙語"]:
            words = text.split(" ")
            lines, current_line = [], []
            for word in words:
                test_line = " ".join(current_line + [word])
                bbox = font.getbbox(test_line)
                test_width = bbox[2] - bbox[0]
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(" ".join(current_line))
        else:
            separators = [":", "：", "、", "，", ","]
            words, current_word = [], ""
            for char in text:
                current_word += char
                if char in separators:
                    words.append(current_word)
                    current_word = ""
            if current_word:
                words.append(current_word)
            lines, current_line = [], []
            for word in words:
                test_line = "".join(current_line + [word])
                bbox = font.getbbox(test_line)
                test_width = bbox[2] - bbox[0]
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append("".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append("".join(current_line))
        return lines

    lines = wrap_text(text, font, max_width, lang)
    bbox = font.getbbox("A")
    line_height = bbox[3] - bbox[1]
    text_height = len(lines) * (line_height + line_spacing) - line_spacing

    while text_height > max_height and font_size > 40:
        font_size -= 5
        font = ImageFont.truetype(font_path, font_size)
        lines = wrap_text(text, font, max_width, lang)
        bbox = font.getbbox("A")
        line_height = bbox[3] - bbox[1]
        text_height = len(lines) * (line_height + line_spacing) - line_spacing

    y_start = position[1]
    positions = [(position[0], y_start + i * (line_height + line_spacing), line) for i, line in enumerate(lines)]
    return font, positions

def step5_draw_styled_text(draw, img, text_positions, font, anchor, step5_effect, width, height):
    use_gradient = step5_effect.get("gradient", False)
    use_stroke = step5_effect.get("stroke", False)
    use_shadow = step5_effect.get("shadow", False)
    use_glow = step5_effect.get("glow", False)

    for x, y, text in text_positions:
        if use_shadow:
            shadow_color = (30, 30, 30)
            shadow_offset = 5
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color, anchor=anchor)
        if use_glow:
            for offset in range(3, 0, -1):
                glow_color = (255, 255, 255)
                draw.text((x + offset, y + offset), text, font=font, fill=glow_color, anchor=anchor)
                draw.text((x - offset, y - offset), text, font=font, fill=glow_color, anchor=anchor)
                draw.text((x + offset, y - offset), text, font=font, fill=glow_color, anchor=anchor)
                draw.text((x - offset, y + offset), text, font=font, fill=glow_color, anchor=anchor)
        if use_stroke:
            stroke_color = (0, 0, 0)
            draw.text((x + 2, y + 2), text, font=font, fill=stroke_color, anchor=anchor)
            draw.text((x - 2, y - 2), text, font=font, fill=stroke_color, anchor=anchor)
            draw.text((x + 2, y - 2), text, font=font, fill=stroke_color, anchor=anchor)
            draw.text((x - 2, y + 2), text, font=font, fill=stroke_color, anchor=anchor)
        if use_gradient:
            img_temp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw_temp = ImageDraw.Draw(img_temp)
            draw_temp.text((x, y), text, font=font, fill=(255, 255, 255, 255), anchor=anchor)
            for y_temp in range(height):
                for x_temp in range(width):
                    if img_temp.getpixel((x_temp, y_temp))[3] > 0:
                        color = step5_get_rainbow_gradient(y_temp, height)
                        draw.point((x_temp, y_temp), fill=color)

def step5_get_story_title(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['title']

def step5_resize_image(img, target_width, target_height):
    orig_width, orig_height = img.size
    target_ratio = target_width / target_height
    orig_ratio = orig_width / orig_height

    if orig_ratio > target_ratio:
        new_width = int(orig_height * target_ratio)
        new_height = orig_height
        left = (orig_width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = new_height
    else:
        new_width = orig_width
        new_height = int(orig_width / target_ratio)
        left = 0
        top = (orig_height - new_height) // 2
        right = new_width
        bottom = top + new_height

    img = img.crop((left, top, right, bottom))
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return img

def step5_process_story_folder(story_folder, width, height, initial_title_font_size, title_position, max_title_width, max_title_height, step5_effect, line_spacing):
    story_name = os.path.basename(story_folder)
    video_folder = os.path.join(story_folder, "故事影片_mp4")
    thumbnail_folder = os.path.join(story_folder, "故事_thumbnail_file")
    intro_folder = os.path.join(story_folder, "故事介紹")
    bg_image_path = os.path.join(thumbnail_folder, "原始圖片.jpg")

    if not (os.path.exists(video_folder) and os.path.exists(intro_folder) and os.path.exists(bg_image_path)):
        print(f"警告：故事 {story_name} 缺少必要資料夾或原始圖片，跳過")
        return

    video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')]
    if not video_files:
        print(f"警告：故事 {story_name} 的故事影片_mp4 資料夾無 .mp4 檔案，跳過")
        return

    for video_file in video_files:
        try:
            parts = video_file.split('_')
            language = parts[1]
            if language not in language_map:
                raise ValueError(f"語言 '{language}' 未在 language_map 中定義")

            lang_code = language_map[language]
            json_file = f"{story_name}_full_intro_{lang_code}.json" if lang_code else f"{story_name}_full_intro.json"
            json_path = os.path.join(intro_folder, json_file)
            if not os.path.exists(json_path):
                print(f"警告：故事 {story_name} 缺少 {json_file}，跳過 {video_file}")
                continue
            title = step5_get_story_title(json_path)

            img = Image.open(bg_image_path)
            img = step5_resize_image(img, width, height)
            img = img.convert("RGBA")
            draw = ImageDraw.Draw(img)

            title_font, title_positions = step5_adjust_text(draw, title, fonts[language], initial_title_font_size, max_title_width, max_title_height, title_position, language, line_spacing)
            print(f"書名位置（{language}）：{title_positions}")

            step5_draw_styled_text(draw, img, title_positions, title_font, "mm", step5_effect, width, height)

            jpg_file = video_file.replace('.mp4', '.jpg')
            output_path = os.path.join(thumbnail_folder, jpg_file)
            img = img.convert("RGB")
            img.save(output_path)
            print(f"已生成封面：{output_path}")
        except Exception as e:
            print(f"處理檔案 {video_file} 時發生錯誤：{type(e).__name__} - {str(e)}")

def step5_main(story_folder):
    width, height = 1280, 720
    initial_title_font_size = 100
    title_position = (width // 2, int(height * 5 / 6))
    max_title_width = width * 0.8
    max_title_height = height * 0.15
    line_spacing = 10
    step5_effect = step5_effects["彩色漸層"]

    step5_process_story_folder(story_folder, width, height, initial_title_font_size, title_position, max_title_width, max_title_height, step5_effect, line_spacing)
    print("所有封面生成完畢！")



# --- 新增的設定 (可放在 Step 6 附近) ---
import pytz
import threading
from datetime import datetime, timedelta, time as dt_time

# 設定時區為台灣
TAIWAN_TZ = pytz.timezone('Asia/Taipei')

# 設定每日小說產量
DAILY_NOVEL_QUOTA = 2

# YT 上傳排程 (台灣時間, 24小時制)
# 格式: '語言': (開始小時, 結束小時)
UPLOAD_SCHEDULE = {
    '繁體中文': (17, 20), # 17:00 - 20:00
    '英文': (1, 4),     # 21:00 - 23:00
    '西班牙語': (4, 8)   # 隔天 02:00 - 05:00
}

# 追蹤已啟動的線程
upload_threads = []

PRODUCTION_START_HOUR = 8  # 早上 6 點
PRODUCTION_END_HOUR = 16   # 下午 5 點


def is_within_upload_window(language, now_tw):
    if language not in UPLOAD_SCHEDULE:
        return False
    start_hour, end_hour = UPLOAD_SCHEDULE[language]
    current_hour = now_tw.hour
    # 處理跨夜間的窗口（如英文1-4是凌晨）
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    else:
        # 跨夜，如西班牙4-8
        return start_hour <= current_hour or current_hour < end_hour
    
   # 新增此函數（收集pending故事）
def collect_pending_stories(base_path, uploaded_path):
    pending = []
    all_stories = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    for story_folder in all_stories:
        story_name = os.path.basename(story_folder)
        uploaded_folder = os.path.join(uploaded_path, story_name)
        if not os.path.exists(uploaded_folder):
            video_dir = os.path.join(story_folder, "故事影片_mp4")
            if os.path.exists(video_dir) and len([f for f in os.listdir(video_dir) if f.endswith(".mp4")]) > 0:
                pending.append(story_folder)
    return pending 



# --- YouTube API 設定 ---
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADED_LOG = os.path.join(BASE_DIR, 'uploaded_videos.txt')

# --- 多語言設定 (已完全還原為您提供的版本) ---

language_config = {
    '繁體中文': {
        'client_secrets': os.path.join(BASE_DIR, 'qaz611440_中文', 'client_secret_63191876355-qdghn7f73bv6ani0va5g173pcd35no2s.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'qaz611440_中文', 'credentials.json')
    },
    '英文': {
        'client_secrets': os.path.join(BASE_DIR, 'zxcasdqwe611440_英文', 'client_secret_684873813321-94tir36rb5sleq2vms7j363mclca2bif.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'zxcasdqwe611440_英文', 'credentials.json')
    },
    '德語': {
        'client_secrets': os.path.join(BASE_DIR, 'qwe611440_德語', 'client_secret_801063156977-ajso0ppgesu64s8tn752fidat71hfkj2.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'qwe611440_德語', 'credentials.json')
    },
    '法語': {
        'client_secrets': os.path.join(BASE_DIR, 'qweasdzxc611440_法語', 'client_secret_655856158787-9dhrm96420pu5mi1lgvui206j4gfgij3.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'qweasdzxc611440_法語', 'credentials.json')
    },
    '西班牙語': {
        'client_secrets': os.path.join(BASE_DIR, 'ewqdsacxz611440_西班牙語', 'client_secret_1089596147414-ne7igfn32g2cbt85f4idme6gfrfavlic.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'ewqdsacxz611440_西班牙語', 'credentials.json')
    },
    '日語': {
        'client_secrets': os.path.join(BASE_DIR, 'cdexswzaq611440_日語', 'client_secret_831089702653-7d5gel5kqah9bjksddng8jsaads81ts7.apps.googleusercontent.com.json'),
        'credentials': os.path.join(BASE_DIR, 'cdexswzaq611440_日語', 'credentials.json')
    },
}

LANGUAGE_ORDER = ['繁體中文', '英文', '德語', '法語', '西班牙語', '日語']
LANGUAGE_ABBR = {
    '繁體中文': '', '英文': 'en', '德語': 'de', '法語': 'fr', '西班牙語': 'es', '日語': 'ja'
}

# 【新增】安全的書名號管理，維持風格同時避免錯誤
LANGUAGE_BOOK_QUOTES = {
    '繁體中文': '《{}》', '日語': '《{}》', # 中文和日語使用《》
    '英文': '"{}"', '德語': '"{}"', '法語': '"{}"', '西班牙語': '"{}"' # 其他語言使用標準引號
}

LANGUAGE_PREFIXES = {
    '繁體中文': '【{}小說】', '英文': '[{} Novel]', '德語': '[{} Roman]', '法語': '[{} Roman]', '西班牙語': '[{} Novela]', '日語': '【{}小説】'
}

LANGUAGE_SHORTS_PREFIXES = {
    '繁體中文': '【短篇預告】【{}小說】', '英文': '[Short Preview][{} Novel]', '德語': '[Kurzvorschau][{} Roman]', '法語': '[Aperçu Court][{} Roman]', '西班牙語': '[Vista Previa Corta][{} Novela]', '日語': '【短編予告】【{}小説】'
}

LANGUAGE_TAGS = {
    '繁體中文': '#小說 #有聲書 #原創',
    '英文': '#Novel #Audiobook #Original',
    '德語': '#Roman #Hörbuch #Original',
    '法語': '#Roman #LivreAudio #Original',
    '西班牙語': '#Novela #Audiolibro #Original',
    '日語': '#小説 #オーディオブック #オリジナル'
}

LANGUAGE_APPEND_INFO = {
    '繁體中文': """
🎧 邊聽邊支持，記得訂閱頻道哦～🙏 感謝你的參與，讓故事更精彩！😊

""",
    '英文': """
🎧 Subscribe while you listen to keep the stories coming! 🙏 Thank you for joining and making every story shine! 😊

""",
    '西班牙語': """
🎧 Suscríbete mientras escuchas para seguir disfrutando de las historias. 🙏 ¡Gracias por participar y hacer que cada historia brille! 😊

"""
}

\

LANGUAGE_SHORTS_LINK_PROMPT = {
    '繁體中文': '完整版連結下方', 
    '英文': 'Full video link below', 
    '德語': 'Link zum vollständigen Video unten', 
    '法語': 'Lien vers la vidéo complète ci-dessous', 
    '西班牙語': 'Enlace al video completo abajo', 
    '日語': '完全版リンクは下に'
}

# -- 以下為國際化設定 (保留優化) --
LANGUAGE_SHORTS_COMMENT_TEXT = {
    '繁體中文': '🌟 完整版影片：{} 🌟', 
    '英文': '🌟 Full video here: {} 🌟', 
    '德語': '🌟 Vollständiges Video hier: {} 🌟', 
    '法語': '🌟 Vidéo complète ici : {} 🌟', 
    '西班牙語': '🌟 Video completo aquí: {} 🌟', 
    '日語': '🌟 完全版ビデオはこちら：{} 🌟'
}
LANGUAGE_SHORTS_COMMENT_PROMPT = {
    '繁體中文': '\n\n📌 查看下方連結，探索完整版影片！',
    '英文': '\n\n📌 Check the link below for the full video!',
    '德語': '\n\n📌 Schau dir den Link unten an, um das vollständige Video zu sehen!',
    '法語': '\n\n📌 Consultez le lien ci-dessous pour découvrir la vidéo complète !',
    '西班牙語': '\n\n📌 ¡Haz clic en el enlace de abajo para ver el video completo!',
    '日語': '\n\n📌 下のリンクをチェックして、完全版ビデオをご覧ください！'
}


def get_wait_seconds_to_window_start(language: str) -> float:
    """
    【新函式】計算從現在到指定語言的下一個上傳窗口「開始」時，需要等待的秒數。
    這個版本沒有隨機性，確保任務在窗口開始時準時啟動。
    """
    if language not in UPLOAD_SCHEDULE:
        return 0.0

    now_tw = datetime.now(TAIWAN_TZ)
    start_hour, _ = UPLOAD_SCHEDULE[language]

    # 計算今天的窗口開始時間
    window_start_time = now_tw.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    # 如果當前時間已經晚於今天的開始時間，則目標是明天的開始時間
    if now_tw >= window_start_time:
        window_start_time += timedelta(days=1)
    
    wait_seconds = (window_start_time - now_tw).total_seconds()
    
    return max(0.0, wait_seconds)

# --- 輔助函式 ---


def normalize_text(text):
    """清理文字，移除多餘空格和不可列印字元。"""
    if not text:
        return ""
    return ''.join(c for c in text.strip() if c.isprintable())

def generate_safe_title(language, novel_type, title, tags, is_short=False):
    """
    【核心優化】生成一個安全且長度合規的 YouTube 標題。
    會自動使用正確的書名號，並智慧地加入標籤和連結提示。
    """

    # 根據是否為 Short 選擇不同的設定
    if is_short:
        prefix = LANGUAGE_SHORTS_PREFIXES[language].format(novel_type)
        link_prompt = LANGUAGE_SHORTS_LINK_PROMPT[language]
        fixed_tags = "#Shorts"
    else:
        prefix = LANGUAGE_PREFIXES[language].format(novel_type)
        link_prompt = ""
        fixed_tags = LANGUAGE_TAGS[language]

    wrapper = LANGUAGE_BOOK_QUOTES.get(language, '"{}"') # 安全地獲取書名號
    wrapped_title = wrapper.format(title)
    
    base_title = f"{prefix} {wrapped_title}"
    
    # 計算剩餘可用長度
    # 預留空格長度: 1(prefix後) + 1(title後) + 1(tags後) + 1(prompt前) = 4
    remaining_len = 100 - (len(base_title) + len(fixed_tags) + len(link_prompt) + 4)
    
    formatted_tags = ' '.join(f"#{tag.strip()}" for tag in tags if tag.strip())
    
    # 智慧截斷標籤
    if len(formatted_tags) > remaining_len:
        if remaining_len > 0:
            formatted_tags = formatted_tags[:remaining_len].rsplit(' ', 1)[0]
        else:
            formatted_tags = "" # 如果沒有空間，則不加標籤

    # 組合最終標題
    parts = [base_title, formatted_tags, fixed_tags, link_prompt]
    final_title = ' '.join(part for part in parts if part).strip()
    
    # 最後做一次保險的截斷
    return final_title[:100]

# --- YouTube API 操作函式 (保留優化) ---
def get_authenticated_service(client_secrets_file, credentials_file):
    creds = None
    if os.path.exists(credentials_file):
        try:
            creds = Credentials.from_authorized_user_file(credentials_file, SCOPES)
        except Exception as e:
            print(f"讀取憑證檔案失敗: {credentials_file}, 錯誤: {e}")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(credentials_file, 'w') as token:
                token.write(creds.to_json())
            print("憑證已自動刷新")
        except Exception as e:
            print(f"刷新憑證失敗，錯誤: {e}")
            creds = None

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(credentials_file, 'w') as token:
                token.write(creds.to_json())
            print("已生成新的憑證")
        except Exception as e:
            print(f"生成新憑證失敗: {client_secrets_file}, 錯誤: {e}")
            return None
    
    if not creds:
        print(f"無法獲取有效憑證，無法建立 YouTube 服務")
        return None

    return build('youtube', 'v3', credentials=creds, cache_discovery=False)

def upload_video(youtube, video_file, title, description, category, tags, privacy_status='public', max_retries=5):
    body = {
        'snippet': {'title': title, 'description': description, 'tags': tags, 'categoryId': category},
        'status': {'privacyStatus': privacy_status}
    }
    media = MediaFileUpload(video_file, chunksize=20*1024*1024, resumable=True) # 增加 chunksize
    
    is_short = "#Shorts" in title
    upload_type = 'Shorts' if is_short else '影片'
    
    print(f"開始上傳 {upload_type}: {os.path.basename(video_file)}")
    print(f"標題: {title}")

    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None
    retry_count = 0
    backoff_time = 10

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f'上傳進度：{int(status.progress() * 100)}%')
            retry_count = 0 
            backoff_time = 10
        except (HttpError, ConnectionError, ssl.SSLEOFError) as e:
            print(f"上傳捕獲到異常: {type(e).__name__} - {e}")
            retry_count += 1
            if retry_count > max_retries:
                print(f"上傳失敗，已超過最大重試次數 ({max_retries})")
                raise
            print(f"上傳中斷，等待 {backoff_time} 秒後重試 ({retry_count}/{max_retries})...")
            time.sleep(backoff_time)
            backoff_time *= 2
            request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

    video_id = response["id"]
    print(f'{upload_type}上傳完成，影片 ID: {video_id}')
    return video_id

def set_thumbnail(youtube, video_id, thumbnail_file):
    try:
        media = MediaFileUpload(thumbnail_file)
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        print(f'縮圖已設置，影片 ID: {video_id}')
    except Exception as e:
        print(f"設置縮圖失敗，影片 ID: {video_id}, 錯誤: {e}")

def get_or_create_playlist(youtube, title, description, privacy_status='public'):
    try:
        request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
        while request:
            response = request.execute()
            for playlist in response.get('items', []):
                if playlist['snippet']['title'] == title:
                    return playlist['id']
            request = youtube.playlists().list_next(request, response)
        
        print(f"找不到播放清單 '{title}', 正在建立新的...")
        response = youtube.playlists().insert(
            part="snippet,status",
            body={"snippet": {"title": title, "description": description}, "status": {"privacyStatus": privacy_status}}
        ).execute()
        return response['id']
    except Exception as e:
        print(f"創建或獲取播放清單失敗，標題: {title}, 錯誤: {e}")
        return None

def add_video_to_playlist(youtube, playlist_id, video_id):
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
        ).execute()
        print(f"影片已添加到播放清單，ID: {playlist_id}")
    except Exception as e:
        print(f"添加影片到播放清單失敗，ID: {playlist_id}, 錯誤: {e}")

def clip_video_to_short(input_path, output_path, duration=59):
    try:
        command = (
            f'"{FFMPEG_PATH_SUBGEN}" -y -i "{input_path}" -t {duration} -vf '
            f'"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1" '
            f'-c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k "{output_path}"'
        )
        print("正在生成 Shorts 影片...")
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"成功生成 Shorts 檔案: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"剪輯 Shorts 失敗: {e.stderr}")
        return None


def is_language_uploaded(story_folder, language):
    """檢查這個語言是否已經上傳完成"""
    flag_file = os.path.join(story_folder, "上傳旗標", f"{language}_已完成.flag")
    return os.path.exists(flag_file)

# --- 主流程函式 (保留優化結構) ---

def execute_upload(info, story, story_path, intro_dir, video_dir, thumbnail_dir):
    """
    這是實際執行單個影片上傳的函數。
    (此函數內容基本來自您原來的 process_single_video)
    """
    language = info['language']
    video_file = os.path.join(video_dir, info['file'])
    
    print(f"\n[{datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}] --- 開始執行上傳: {language} | {info['file']} ---")

    # 讀取 JSON 資料
    abbr = LANGUAGE_ABBR.get(language, '')
    json_file = os.path.join(intro_dir, f"{story}_full_intro_{abbr}.json" if abbr else f"{story}_full_intro.json")
    if not os.path.exists(json_file):
        print(f"JSON 檔案不存在，上傳中止: {json_file}")
        return
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            intro_data = json.load(f)
    except Exception as e:
        print(f"讀取 JSON 檔案失敗: {json_file}, 錯誤: {e}")
        return

    # 清理和準備資料 (與您原版相同)
    title = normalize_text(intro_data['title'])
    description = intro_data['description']
    tags = [normalize_text(tag) for tag in intro_data['tags']]
    novel_playlist_title = normalize_text(intro_data['novel_playlist_title'])
    novel_playlist_description = normalize_text(intro_data['novel_playlist_description'])
    category = intro_data.get('category', '22')

    if not title:
        print(f"錯誤：標題無效或為空，JSON 檔案: {json_file}")
        return
        
    novel_type = tags[0] if tags else "Unknown"

    # 取得認證 (與您原版相同)
    config = language_config.get(language)
    if not config or not os.path.exists(config['client_secrets']):
        print(f"語言 '{language}' 的客戶端秘密檔案配置不正確或不存在，跳過。")
        return
    youtube = get_authenticated_service(config['client_secrets'], config['credentials'])
    if not youtube:
        print(f"無法建立 YouTube 服務，跳過影片: {video_file}")
        return

    try:
        # 1. 處理並上傳長影片
        long_title = generate_safe_title(language, novel_type, title, tags, is_short=False)
        long_description = f"{description}\n{LANGUAGE_APPEND_INFO.get(language, '')}\n{' '.join(['#'+t for t in tags])} {LANGUAGE_TAGS[language]}"
        thumbnail_file = os.path.join(thumbnail_dir, info['file'].replace('.mp4', '.jpg'))
        if not os.path.exists(thumbnail_file):
            print(f"縮圖檔案不存在: {thumbnail_file}, 跳過")
            return

        video_id = upload_video(youtube, video_file, long_title, long_description, category, tags, 'public')
        long_video_url = f"https://www.youtube.com/watch?v={video_id}"
        set_thumbnail(youtube, video_id, thumbnail_file)
        
        playlist_id = get_or_create_playlist(youtube, novel_playlist_title, novel_playlist_description)
        if playlist_id:
            add_video_to_playlist(youtube, playlist_id, video_id)
        print(f"成功上傳長影片: {long_video_url}")
        # === 新增：上傳成功後寫入旗標檔 ===
        flag_dir = os.path.join(story_path, "上傳旗標")
        os.makedirs(flag_dir, exist_ok=True)
        flag_file = os.path.join(flag_dir, f"{language}_已完成.flag")
        with open(flag_file, "w", encoding="utf-8") as f:
            f.write(datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d %H:%M:%S"))
        print(f"[{language}] 上傳完成，旗標檔已建立: {flag_file}")

        # 2. 生成並上傳 Shorts
        short_video_path = os.path.join(video_dir, info['file'].replace('.mp4', '_short.mp4'))
        if not clip_video_to_short(video_file, short_video_path):
            print(f"無法生成 Shorts，跳過 Shorts 處理: {video_file}")
            return
            
        short_title = generate_safe_title(language, novel_type, title, tags, is_short=True)
        short_description_body = f"{intro_data['description'][:500]}..." if len(intro_data['description']) > 500 else intro_data['description']
        prompt_text = LANGUAGE_SHORTS_COMMENT_PROMPT[language]
        comment_template = LANGUAGE_SHORTS_COMMENT_TEXT[language]
        link_text = comment_template.format(long_video_url)
        final_short_description = f"{short_description_body}\n{LANGUAGE_APPEND_INFO.get(language, '')}\n{prompt_text}\n{link_text}\n{' '.join(['#'+t for t in tags])} {LANGUAGE_TAGS[language]} #Shorts"
        short_video_id = upload_video(youtube, short_video_path, short_title, final_short_description, '24', tags + ['Shorts'], 'public')
        print(f"成功上傳 Shorts: https://www.youtube.com/shorts/{short_video_id}")

        # 3. 清理 Shorts 檔案
        try:
            os.remove(short_video_path)
            print(f"已刪除 Shorts 檔案: {short_video_path}")
        except Exception as e:
            print(f"刪除 Shorts 檔案失敗: {short_video_path}, 錯誤: {e}")

    except HttpError as e:
        print(f"處理失敗 (HttpError): {video_file}, 狀態碼: {e.resp.status}, 原因: {e.content.decode('utf-8')}")
        if e.resp.status == 403:
            print("錯誤 403: Forbidden。可能原因為 API 配額已用盡，腳本將終止。")
            raise SystemExit("YouTube API quota likely exceeded.")
    except Exception as e:
        import traceback
        print(f"處理失敗 (一般錯誤): {video_file}, 錯誤類型: {type(e).__name__}, 錯誤訊息: {e}")
        traceback.print_exc()


# 【新增】的函數，用於控制單一語言的影片上傳順序

def run_sequential_upload_pipeline(list_of_story_folders: list):
    """
    【新函式】執行一個完全線性的、阻塞式的上傳流程。
    嚴格按照 簡中 -> 英文 -> 西班牙文 的順序處理。
    """
    print("\n==================== 開始執行線性上傳流水線 ====================")
    
    # 語言處理順序
    language_order = ['繁體中文', '英文', '西班牙語']
    
    # 每個語言內的影片上傳間隔（秒）
    upload_interval_seconds = 4800 # 1.5小時

    for language in language_order:
        # 1. 從今天生成的所有故事中，收集該語言的全部影片
        videos_for_this_language = []
        print(f"\n--- 正在收集 [{language}] 的影片 ---")
        for story_folder in list_of_story_folders:
            story_name = os.path.basename(story_folder)
            video_dir = os.path.join(story_folder, '故事影片_mp4')
            intro_dir = os.path.join(story_folder, '故事介紹')
            thumbnail_dir = os.path.join(story_folder, '故事_thumbnail_file')

            if not os.path.isdir(video_dir):
                continue
            
            for video_file in os.listdir(video_dir):
                # 檔名格式: {story_name}_{language}_{voice}.mp4
                try:
                    lang_from_file = video_file.split('_')[-2]
                    if lang_from_file == language and '_short' not in video_file:
                        video_info = {
                            'language': language,
                            'file': video_file,
                            'story': story_name,
                            'story_path': story_folder,
                            'intro_dir': intro_dir,
                            'video_dir': video_dir,
                            'thumbnail_dir': thumbnail_dir
                        }
                        videos_for_this_language.append(video_info)
                        print(f"找到影片: {video_file}")
                except IndexError:
                    continue # 檔名不符，跳過

        if not videos_for_this_language:
            print(f"未找到 [{language}] 的影片，跳至下一語言。")
            continue

        print(f"[{language}] 共找到 {len(videos_for_this_language)} 部影片，準備進入上傳排程。")

        # 2. 等待到達該語言的上傳時間窗口
        wait_seconds = get_wait_seconds_to_window_start(language)
        if wait_seconds > 0:
            print(f"[{language}] 等待 {wait_seconds/3600:.2f} 小時，將於 "
                  f"{(datetime.now(TAIWAN_TZ) + timedelta(seconds=wait_seconds)).strftime('%Y-%m-%d %H:%M')} "
                  f"開始上傳。")
            time.sleep(wait_seconds)
        
        # 3. 依次上傳該語言的所有影片，每個之間間隔1小時
        print(f"\n[{language}] 時間到達，開始上傳流程...")
        for i, video_info in enumerate(videos_for_this_language):
            # 第一部影片直接上傳，後續影片需要等待間隔
            if i > 0:
                # 增加一個小的隨機值，讓等待時間不那麼固定
                interval = upload_interval_seconds + random.uniform(1, 300)
                print(f"[{language}] 上一部影片已處理完畢。等待 {interval/60:.1f} 分鐘後上傳下一部...")
                time.sleep(interval)
            
            # 呼叫單個影片的上傳函式
            print(f"[{language} | {i+1}/{len(videos_for_this_language)}] 開始處理影片: {video_info['file']}")
            try:
                # 注意，這裡我們把所有需要的路徑都從 video_info 傳遞給 execute_upload
                execute_upload(
                    video_info, 
                    video_info['story'], 
                    video_info['story_path'], 
                    video_info['intro_dir'], 
                    video_info['video_dir'], 
                    video_info['thumbnail_dir']
                )
            except Exception as e:
                import traceback
                print(f"上傳影片 {video_info['file']} 時發生嚴重錯誤: {e}")
                traceback.print_exc()
                # 即使出錯，也繼續處理下一個影片，避免流程卡死
                continue
        
        print(f"--- [{language}] 的所有影片均已處理完畢 ---")

    print("\n==================== 所有語言的上傳流水線已全部執行完畢 ====================")


# 執行單個小說的後續步驟
def find_newest_story_folder(base_path, existing_folders):
    """從基礎路徑中找出最新的資料夾"""
    current_folders = set(os.listdir(base_path))
    new_folders = current_folders - existing_folders
    if not new_folders:
        return None
    # 返回最新創建的資料夾
    return max(
        [os.path.join(base_path, d) for d in new_folders],
        key=os.path.getctime
    )

# 修改原 run_daily_automation（替換整個函數）
def run_daily_automation():
    """
    【修改版】全自動化主控流程，採用嚴格的線性、阻塞式設計。
    """
    print("="*40)
    print("=== 全自動小說生產與上傳系統 (V4-Sequential) 已啟動 ===")
    print(f"=== 每日目標: {DAILY_NOVEL_QUOTA} 部小說 ===")
    print(f"=== 生產窗口: {PRODUCTION_START_HOUR:02}:00 - {PRODUCTION_END_HOUR:02}:00 (台灣時間) ===")
    print("="*40)

    try:
        while not SHUTDOWN_REQUESTED:
            now_tw = datetime.now(TAIWAN_TZ)

            # 新增: 先處理pending stories (無論是否在生產窗口，重啟時優先)
            # === 完全替換 pending 處理區塊 ===
            # === 永久正確版 pending 處理（旗標檔模式）===
            pending_stories = collect_pending_stories(BASE_PATH, UPLOADED_PATH)
            if pending_stories:
                now_dt = datetime.now(TAIWAN_TZ)
                print(f"\n[{now_dt.strftime('%Y-%m-%d %H:%M:%S')}] 偵測到 {len(pending_stories)} 個待上傳的故事，開始檢查旗標...")
                
                for story_folder in pending_stories:
                    story_name = os.path.basename(story_folder)
                    video_dir = os.path.join(story_folder, '故事影片_mp4')
                    if not os.path.isdir(video_dir):
                        continue
                        
                    videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4') and '_short' not in f]
                    need_upload = []  # 還要上傳的影片

                    for video_file in videos:
                        try:
                            lang = video_file.split('_')[-2]
                        except:
                            continue
                            
                        if is_language_uploaded(story_folder, lang):
                            print(f"[{lang}] 已上傳過，跳過 {video_file}")
                            continue
                            
                        # 檢查現在是否在這個語言的窗口內
                        if is_within_upload_window(lang, now_dt):
                            print(f"[{lang}] 旗標未建立 + 正在窗口內 → 立即上傳 {video_file}")
                            video_info = {
                                'language': lang,
                                'file': video_file,
                                'story': story_name,
                                'story_path': story_folder,
                                'intro_dir': os.path.join(story_folder, '故事介紹'),
                                'video_dir': video_dir,
                                'thumbnail_dir': os.path.join(story_folder, '故事_thumbnail_file')
                            }
                            execute_upload(video_info, story_name, story_folder,
                                         video_info['intro_dir'], video_dir, video_info['thumbnail_dir'])
                        else:
                            print(f"[{lang}] 旗標未建立，但尚未到窗口時間，保留等待")
                            need_upload.append(lang)

                    # 只有當所有語言都已有旗標檔，才搬走資料夾
                    if not need_upload and all(is_language_uploaded(story_folder, video_file.split('_')[-2]) 
                                             for video_file in videos if '_' in video_file):
                        print(f"故事 {story_name} 所有語言均已上傳完成，移動到已上傳資料夾")
                        dest = os.path.join(UPLOADED_PATH, story_name)
                        os.makedirs(UPLOADED_PATH, exist_ok=True)
                        shutil.move(story_folder, dest)
                        print(f"已移動: {story_folder} → {dest}")
                    else:
                        print(f"故事 {story_name} 還有語言待上傳，保留資料夾")

            # --- 1. 檢查是否在生產窗口 --- (原邏輯繼續...)
            production_start_time = now_tw.replace(hour=PRODUCTION_START_HOUR, minute=0, second=0, microsecond=0)
            production_end_time = now_tw.replace(hour=PRODUCTION_END_HOUR, minute=0, second=0, microsecond=0)

            if production_start_time <= now_tw < production_end_time:
                print(f"\n[{now_tw.strftime('%Y-%m-%d %H:%M:%S')}] 進入生產窗口，開始處理小說...")
                
                # --- 2. 生產階段：連續生成當日所有小說 ---
                novels_produced_today = [] # 用來收集今天所有生成的故事資料夾路徑
                novels_to_process = 0
                while novels_to_process < DAILY_NOVEL_QUOTA and not SHUTDOWN_REQUESTED:
                    if datetime.now(TAIWAN_TZ) >= production_end_time:
                        print("生產時間窗口已結束，今日生產提前終止。")
                        break
                    
                    print(f"\n--- 正在處理今日第 {novels_to_process + 1} / {DAILY_NOVEL_QUOTA} 部小說 ---")

                    try:
                        # Step 1: 生成小說
                        print("Step 1: 生成小說內容...")
                        folders_before = set(os.listdir(BASE_PATH))
                        自動化極短篇小說測試V31_20251117.run_novel_generation_pipeline()
                        time.sleep(5) 
                        story_folder = find_newest_story_folder(BASE_PATH, folders_before)
                        
                        if not story_folder or not os.path.isdir(story_folder):
                            print("錯誤：未能找到新生成的小說資料夾，將在 60 秒後重試...")
                            time.sleep(60)
                            continue
                        
                        story_name = os.path.basename(story_folder)
                        print(f"Step 1 完成，新故事: {story_name}")

                        # Step 1.5 - 5: 素材處理
                        print(f"開始處理故事 {story_name} 的後續步驟...")
                        step1_5_main(story_folder)
                        step2_main(story_folder)
                        step3_main(story_folder, story_name)
                        step4_main(story_folder)
                        step4_5_generate_subtitles_and_embed(story_folder)
                        step5_main(story_folder)
                        
                        print(f"故事 {story_name} 的素材已全部準備就緒。")
                        novels_produced_today.append(story_folder)
                        novels_to_process += 1

                    except Exception as e:
                        import traceback
                        print(f"處理故事過程中發生嚴重錯誤: {e}")
                        traceback.print_exc()
                        print("此故事處理失敗，將嘗試生成下一部。")
                        continue
                
                print(f"\n--- 今日共生成 {len(novels_produced_today)} 部小說，生產階段結束。---")

                # --- 3. 上傳階段：執行線性上傳流水線 ---
                if novels_produced_today:
                    # 這個函式會阻塞，直到所有語言的所有影片都上傳完畢
                    run_sequential_upload_pipeline(novels_produced_today)
                
                    # --- 4. 清理階段：所有上傳完成後，移動資料夾 ---
                    print("\n--- 所有上傳任務已完成，開始清理已處理的故事資料夾 ---")
                    for story_folder_path in novels_produced_today:
                        story_name = os.path.basename(story_folder_path)
                        try:
                            destination_folder_path = os.path.join(UPLOADED_PATH, story_name)
                            if not os.path.exists(UPLOADED_PATH):
                                os.makedirs(UPLOADED_PATH)
                            shutil.move(story_folder_path, destination_folder_path)
                            print(f"資料夾已移動: {story_name} -> {destination_folder_path}")
                        except Exception as e:
                            print(f"移動資料夾 {story_name} 失敗: {e}")
                    print("清理階段完成。")
            
# --- 5. 智慧休眠階段：根據是否有 pending 上傳任務決定睡到哪裡 ---
            now_tw = datetime.now(TAIWAN_TZ)
            
            # Step 1: 檢查是否有任何語言還沒上傳（旗標檔不存在）且窗口在未來
            pending_stories = collect_pending_stories(BASE_PATH, UPLOADED_PATH)
            next_wakeup_time = None  # 預設睡到明天生產時間

            if pending_stories:
                print(f"\n[{now_tw.strftime('%Y-%m-%d %H:%M:%S')}] 正在計算最近的待上傳窗口...")
                candidate_times = []

                for story_folder in pending_stories:
                    video_dir = os.path.join(story_folder, '故事影片_mp4')
                    if not os.path.isdir(video_dir):
                        continue
                    for video_file in os.listdir(video_dir):
                        if '_short' in video_file or not video_file.endswith('.mp4'):
                            continue
                        try:
                            lang = video_file.split('_')[-2]
                        except:
                            continue

                        # 如果這個語言已經上傳過，就跳過
                        if is_language_uploaded(story_folder, lang):
                            continue

                        # 計算這個語言的下一個窗口開始時間
                        start_h, end_h = UPLOAD_SCHEDULE[lang]
                        candidate = now_tw.replace(hour=start_h, minute=0, second=0, microsecond=0)

                        # 跨夜窗口處理（英文 1~4、西班牙語 4~8）
                        if end_h <= start_h:  # 代表是凌晨窗口
                            if now_tw.hour >= start_h:  # 已經過了今天的凌晨窗口 → 明天
                                candidate += timedelta(days=1)
                        else:
                            if now_tw >= candidate.replace(hour=end_h):
                                candidate += timedelta(days=1)  # 今天窗口已過 → 明天

                        candidate_times.append(candidate)

                if candidate_times:
                    next_wakeup_time = min(candidate_times)
                    print(f"偵測到待上傳任務，最早窗口開始時間: {next_wakeup_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Step 2: 如果沒有 pending 上傳任務，就睡到明天生產窗口
            if next_wakeup_time is None:
                next_production = now_tw.replace(hour=PRODUCTION_START_HOUR, minute=0, second=0, microsecond=0)
                if now_tw >= next_production:
                    next_production += timedelta(days=1)
                next_wakeup_time = next_production
                print(f"無待上傳任務，休眠至下一個生產窗口: {next_wakeup_time.strftime('%Y-%m-%d %H:%M:%S')}")

            wait_seconds = max(60, (next_wakeup_time - now_tw).total_seconds())
            hours_to_wait = wait_seconds / 3600

            print(f"\n[{now_tw.strftime('%Y-%m-%d %H:%M:%S')}] 進入休眠，預計醒來時間: {next_wakeup_time.strftime('%Y-%m-%d %H:%M:%S')} ({hours_to_wait:.2f} 小時後)")

            # 分段睡眠，支援 Ctrl+C 優雅關閉
            sleep_end_time = datetime.now() + timedelta(seconds=wait_seconds)
            while datetime.now() < sleep_end_time and not SHUTDOWN_REQUESTED:
                time.sleep(60)
                
                # 每分鐘醒來一次，檢查是否有新任務（可選優化）
                # 如果在休眠中生成了新小說，也能提早醒來處理
                current_pending = collect_pending_stories(BASE_PATH, UPLOADED_PATH)
                if len(current_pending) > len(pending_stories):  # 有新故事生成
                    print(f"偵測到新生成的故事，提前醒來處理！")
                    break

    except KeyboardInterrupt:
        print("\n檢測到手動中斷 (Ctrl+C)，正在優雅關閉程序...")
    except Exception as e:
        import traceback
        print(f"主控流程發生致命錯誤: {e}")
        traceback.print_exc()
    finally:
        print("程序已終止。")


# --- 確保主入口點調用新的主控流程 ---
if __name__ == "__main__":
    # 清理舊線程（如果需要）
    # 執行新的自動化流程
    signal.signal(signal.SIGINT, graceful_shutdown_handler)

    # 執行新的自動化流程
    run_daily_automation()