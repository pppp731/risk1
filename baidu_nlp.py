# -*- coding: utf-8 -*-
"""
Baidu NLP Sentiment Analysis Client
Provides high-precision Chinese sentiment analysis
"""

import json
import requests
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class BaiduNLPClient:
    """Baidu NLP API Client"""

    AUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"
    SENTIMENT_URL = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify"

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = None
        self.token_expire_time = None

    def _get_access_token(self) -> str:
        """Get access token (with caching)"""
        if self.access_token and self.token_expire_time and datetime.now() < self.token_expire_time:
            return self.access_token

        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        try:
            response = requests.post(self.AUTH_URL, params=params, timeout=10)
            result = response.json()

            if "access_token" in result:
                self.access_token = result["access_token"]
                expires_in = result.get("expires_in", 2592000)
                self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 3600)
                return self.access_token
            else:
                error_msg = result.get("error_description", "Unknown error")
                raise Exception(f"Failed to get access_token: {error_msg}")

        except Exception as e:
            raise Exception(f"Baidu NLP auth failed: {str(e)}")

    def analyze_sentiment(self, text: str, retry: int = 2) -> Dict:
        """Sentiment Analysis with retry logic for QPS limit"""
        if not text or not text.strip():
            return {
                "sentiment": 1,
                "confidence": 0,
                "positive_prob": 0.33,
                "negative_prob": 0.33,
                "sentiment_label": "中性"
            }

        # Text length limit
        text = text.strip()[:700]
        access_token = self._get_access_token()
        url = f"{self.SENTIMENT_URL}?access_token={access_token}"

        headers = {"Content-Type": "application/json"}
        payload = {"text": text}

        # Retry logic
        for attempt in range(retry + 1):
            try:
                # Delay to avoid QPS limit
                if attempt > 0:
                    time.sleep(1)
                else:
                    time.sleep(0.5)

                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    timeout=10
                )
                result = response.json()

                if "error_code" in result:
                    error_msg = result.get("error_msg", "Unknown error")
                    # Check if QPS limit
                    if ("qps" in error_msg.lower() or "limit" in error_msg.lower()) and attempt < retry:
                        continue
                    raise Exception(f"Baidu NLP API error: {error_msg}")

                items = result.get("items", [])
                if items:
                    item = items[0]
                    sentiment = item.get("sentiment", 1)
                    label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
                    label_map_cn = {"Negative": "负面", "Neutral": "中性", "Positive": "正面"}

                    en_label = label_map.get(sentiment, "Neutral")
                    return {
                        "sentiment": sentiment,
                        "confidence": item.get("confidence", 0),
                        "positive_prob": item.get("positive_prob", 0),
                        "negative_prob": item.get("negative_prob", 0),
                        "sentiment_label": label_map_cn.get(en_label, "中性")
                    }
                else:
                    return {
                        "sentiment": 1,
                        "confidence": 0,
                        "positive_prob": 0.33,
                        "negative_prob": 0.33,
                        "sentiment_label": "Neutral"
                    }

            except requests.exceptions.RequestException as e:
                raise Exception(f"Baidu NLP request failed: {str(e)}")
            except Exception as e:
                if "qps" in str(e).lower() and attempt < retry:
                    continue
                raise Exception(f"Sentiment analysis failed: {str(e)}")

        raise Exception("Max retries exceeded")


def is_chinese_text(text: str) -> bool:
    """Detect if text contains Chinese characters"""
    if not text:
        return False
    # Check for CJK characters
    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            return True
    return False


class SentimentAnalyzer:
    """Intelligent Sentiment Analyzer - Auto select Baidu NLP (CN) or TextBlob (EN)"""

    def __init__(self, baidu_api_key: str = None, baidu_secret_key: str = None):
        self.baidu_client = None
        self._textblob_available = False

        # Try Baidu NLP
        if baidu_api_key and baidu_secret_key:
            try:
                self.baidu_client = BaiduNLPClient(baidu_api_key, baidu_secret_key)
                print("[Sentiment] Baidu NLP client initialized")
            except Exception as e:
                print(f"[Sentiment] Baidu NLP init failed: {e}")

        # Try TextBlob
        try:
            from textblob import TextBlob
            self._textblob_available = True
        except ImportError:
            pass

    def analyze(self, text: str) -> Dict:
        """Analyze sentiment with automatic language detection"""
        if not text or not text.strip():
            return {
                "polarity": 0,
                "subjectivity": 0,
                "sentiment_label": "Neutral",
                "confidence": 0,
                "source": "none"
            }

        is_chinese = is_chinese_text(text)

        # Chinese -> Baidu NLP (primary) or SnowNLP (fallback)
        if is_chinese:
            if self.baidu_client:
                try:
                    result = self.baidu_client.analyze_sentiment(text)
                    polarity_map = {0: -1.0, 1: 0.0, 2: 1.0}
                    polarity = polarity_map.get(result["sentiment"], 0.0)

                    if result["sentiment"] == 0:
                        polarity = -result["negative_prob"]
                    elif result["sentiment"] == 2:
                        polarity = result["positive_prob"]

                    return {
                        "polarity": round(polarity, 3),
                        "subjectivity": round(result["confidence"], 3),
                        "sentiment_label": result["sentiment_label"],
                        "confidence": round(result["confidence"], 3),
                        "positive_prob": round(result["positive_prob"], 3),
                        "negative_prob": round(result["negative_prob"], 3),
                        "source": "baidu_nlp"
                    }
                except Exception as e:
                    print(f"[Sentiment] Baidu failed, trying SnowNLP: {e}")
                    return self._analyze_with_snownlp(text)
            else:
                # No Baidu client, use SnowNLP directly
                return self._analyze_with_snownlp(text)

        elif self._textblob_available:
            return self._analyze_with_textblob(text)

        return {
            "polarity": 0,
            "subjectivity": 0,
            "sentiment_label": "中性",
            "confidence": 0,
            "source": "none"
        }

    def _analyze_with_snownlp(self, text: str) -> Dict:
        """Analyze Chinese using SnowNLP (offline)"""
        try:
            from snownlp import SnowNLP
            s = SnowNLP(text)
            sentiment = s.sentiments  # 0-1, >0.5 positive

            # Convert to -1 to 1 polarity
            polarity = (sentiment - 0.5) * 2

            if sentiment > 0.6:
                label = "正面"
            elif sentiment < 0.4:
                label = "负面"
            else:
                label = "中性"

            return {
                "polarity": round(polarity, 3),
                "subjectivity": round(abs(polarity), 3),
                "sentiment_label": label,
                "confidence": round(abs(polarity), 3),
                "positive_prob": round(sentiment, 3),
                "negative_prob": round(1 - sentiment, 3),
                "source": "snownlp"
            }
        except Exception as e:
            print(f"[Sentiment] SnowNLP failed: {e}")
            return self._analyze_with_textblob(text)

    def _analyze_with_textblob(self, text: str) -> Dict:
        """Analyze using TextBlob"""
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            if polarity > 0.1:
                label = "正面"
            elif polarity < -0.1:
                label = "负面"
            else:
                label = "中性"

            return {
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "sentiment_label": label,
                "confidence": round(abs(polarity), 3),
                "source": "textblob"
            }
        except Exception as e:
            return {
                "polarity": 0,
                "subjectivity": 0,
                "sentiment_label": "中性",
                "confidence": 0,
                "source": "error"
            }