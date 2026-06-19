from __future__ import annotations

import csv
import calendar
import html
import json
import queue
import re
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    pd = None
    yf = None


TRAIT_MOVER = "mover"
TRAIT_EMA_BULLISH = "ema_bullish"
TRAIT_TIGHT_RANGE = "tight_range"
TRAIT_BOX_BREAKOUT = "box_breakout"
MATCH_ANY = "Any Selected"
MATCH_ALL = "All Selected"
LANG_EN = "en"
LANG_ZH = "zh"

TRAIT_LABELS_BY_LANG = {
    LANG_EN: {
        TRAIT_MOVER: "+10% high-turnover mover",
        TRAIT_EMA_BULLISH: "EMA5/10/20 bullish for 5D+",
        TRAIT_TIGHT_RANGE: "3D+ tight 5% price range",
        TRAIT_BOX_BREAKOUT: "20D high-turnover box breakout",
    },
    LANG_ZH: {
        TRAIT_MOVER: "当日放量大涨10%+",
        TRAIT_EMA_BULLISH: "EMA5/10/20连续多头",
        TRAIT_TIGHT_RANGE: "连续窄幅波动",
        TRAIT_BOX_BREAKOUT: "放量突破箱体",
    },
}
TRAIT_LABELS = TRAIT_LABELS_BY_LANG[LANG_EN]

DISPLAY_COLUMNS = [
    "symbol",
    "last_date",
    "match_count",
    "matched_traits",
    "close",
    "move_pct",
    "gap_pct",
    "mover_ratio",
    "turnover",
    "market_cap",
    "box_width_pct",
    "breakout_side",
    "ema5",
    "ema10",
    "ema20",
    "ema_bullish_days",
    "range_width_pct",
    "range_days",
]

NEWS_COLUMNS = [
    "symbol",
    "time",
    "category",
    "source",
    "headline",
    "summary",
]

NEWS_ALL = "all"
NEWS_TECH_COMPANY = "tech_company"
NEWS_TECH_EVENTS = "tech_events"
NEWS_INDUSTRY_POLICY = "industry_policy"
NEWS_GEOPOLITICS = "geopolitics"
NEWS_MARKET_VIEWS = "market_views"
NEWS_BANK_RESEARCH = "bank_research"
NEWS_SEC_RULES = "sec_rules"
NEWS_EXCHANGE_RULES = "exchange_rules"
NEWS_FED = "fed"
NEWS_HOT_TOPICS = "hot_topics"

NEWS_CATEGORY_ORDER = [
    NEWS_TECH_COMPANY,
    NEWS_TECH_EVENTS,
    NEWS_INDUSTRY_POLICY,
    NEWS_GEOPOLITICS,
    NEWS_MARKET_VIEWS,
    NEWS_BANK_RESEARCH,
    NEWS_SEC_RULES,
    NEWS_EXCHANGE_RULES,
    NEWS_FED,
    NEWS_HOT_TOPICS,
]

NEWS_DAY_RANGE_OPTIONS = ["1", "3", "5", "7", "14", "30", "60", "90"]
SUMMARY_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
GOOGLE_TECH_UPDATE_SEARCHES = [
    '(launches OR unveils OR introduces OR "now available" OR "globally available") (AI OR software OR platform OR technology)',
    'accounts globally available gaming',
    '(MOSFET OR semiconductor OR "silicon carbide" OR processor OR chip) (launches OR unveils OR introduces OR "new benchmark")',
    '(CEO OR CFO OR CTO OR COO OR director OR executive) ("buys shares" OR "insider buying" OR "increases stake") technology',
    '("new business model" OR "subscription model" OR "advertising model" OR "licensing model" OR "monetization model") technology',
]

GOOGLE_FOCUSED_TOPIC_SEARCHES = {
    NEWS_MARKET_VIEWS: [
        '(CEO OR investor OR "fund manager") (interview OR says OR warns OR outlook OR letter) markets',
        '("Fortune 500" OR billionaire) (CEO OR investor) (views OR interview OR outlook)',
    ],
    NEWS_BANK_RESEARCH: [
        '("Goldman Sachs" OR "Morgan Stanley" OR JPMorgan OR "Bank of America" OR Citi) (research OR outlook OR forecast OR recommends)',
    ],
}

NEWS_TOPIC_SEARCHES = {
    NEWS_TECH_EVENTS: [
        "NVIDIA GTC",
        "CES technology",
        "WWDC",
    ],
    NEWS_INDUSTRY_POLICY: [
        "CHIPS Act",
        "US export controls",
        "China semiconductor policy",
    ],
    NEWS_GEOPOLITICS: [
        "sanctions",
        "tariffs",
        "trade war",
    ],
    NEWS_MARKET_VIEWS: [
        "Warren Buffett",
        "Ray Dalio",
        "Jamie Dimon",
        "Howard Marks investor",
        "Michael Burry",
        "Bill Ackman",
        "Cathie Wood",
        "Stanley Druckenmiller",
    ],
    NEWS_BANK_RESEARCH: [
        "Goldman Sachs",
        "Morgan Stanley",
        "JPMorgan",
        "Bank of America",
        "Citi",
        "Wells Fargo",
        "UBS",
        "Barclays",
        "Deutsche Bank",
        "Jefferies",
        "Evercore ISI",
        "Bernstein",
    ],
    NEWS_SEC_RULES: ["SEC"],
    NEWS_EXCHANGE_RULES: [
        "Nasdaq",
        "NYSE",
        "Cboe",
    ],
    NEWS_FED: ["Federal Reserve", "FOMC"],
    NEWS_HOT_TOPICS: ["stock market", "AI stocks", "semiconductor stocks"],
}

NEWS_CATEGORY_KEYWORDS = {
    NEWS_TECH_EVENTS: [
        "conference", "expo", "exhibition", "forum", "summit", "keynote", "symposium",
        "developer conference", "ces", "computex", "mobile world congress", "wwdc", "gtc",
    ],
    NEWS_INDUSTRY_POLICY: [
        "industrial policy", "industry policy", "chips act", "subsidy", "subsidies", "export control",
        "technology policy", "semiconductor policy", "ai policy", "manufacturing policy",
    ],
    NEWS_GEOPOLITICS: [
        "war", "conflict", "sanction", "sanctions", "counter-sanction", "retaliatory measures",
        "tariff", "tariffs", "trade war", "geopolitical", "export ban", "import ban",
    ],
    NEWS_MARKET_VIEWS: [
        "interview", "outlook", "view", "views", "opinion", "predicts", "expects", "warns", "says",
        "shareholder letter", "annual letter", "market call", "investment thesis", "according to",
    ],
    NEWS_BANK_RESEARCH: [
        "research", "industry report", "sector report", "outlook", "strategy report", "thematic report",
        "analyst report", "market strategy", "investment bank", "spots", "favors", "recommends", "expects",
        "raises", "cuts", "upgrades", "downgrades", "tells investors",
    ],
    NEWS_SEC_RULES: [
        "sec rule", "sec rules", "sec regulation", "sec proposal", "securities and exchange commission",
        "final rule", "proposed rule",
    ],
    NEWS_EXCHANGE_RULES: [
        "exchange rule", "listing rule", "trading rule", "market rule", "rule filing", "rule change",
        "listing standard", "trading standard",
    ],
    NEWS_FED: [
        "federal reserve", "fomc", "fed chair", "fed governor", "fed policy", "fed meeting",
        "interest rates", "rate decision", "beige book",
    ],
}

TECH_EVENT_KEYWORDS = [
    "new technology", "new product", "launch", "launches", "launched", "unveil", "unveils", "debut",
    "introduces", "rolls out", "globally available", "now available", "rollout", "sets new benchmark",
]
TECH_ANNOUNCE_KEYWORDS = ["announces", "announcement", "releases", "released"]
TECH_NEWNESS_KEYWORDS = ["new", "next-gen", "next generation", "latest", "advanced"]
TECH_PRODUCT_KEYWORDS = [
    "ai", "product", "platform", "chip", "processor", "model", "software", "hardware", "service",
    "system", "infrastructure",
    "mosfet", "semiconductor", "silicon carbide",
]
EXECUTIVE_ROLE_KEYWORDS = [
    "ceo", "cfo", "cto", "coo", "chief executive", "chief financial", "chief technology", "chief operating",
    "director", "chairman", "executive", "officer", "insider",
]
EXECUTIVE_BUY_KEYWORDS = [
    "insider purchase", "insider buying", "buys shares", "bought shares", "purchases shares", "purchased shares",
    "acquires shares", "acquired shares", "increases stake", "increased stake", "boosts stake", "adds to stake",
]
BUSINESS_MODEL_KEYWORDS = [
    "new business model", "business model", "subscription model", "advertising model", "licensing model",
    "monetization model", "revenue model", "usage-based pricing", "freemium", "marketplace model",
    "commercial model", "new monetization", "monetization strategy",
]
US_PRIMARY_EQUITY_EXCHANGES = {"NMS", "NGM", "NCM", "NYQ", "ASE"}
_US_TECH_COMPANY_ALIASES: list[tuple[str, str, str]] | None = None
TECH_INDUSTRY_KEYWORDS = [
    "software", "semiconductor", "computer", "internet", "electronic", "technology", "cybersecurity",
    "information technology", "consumer electronics", "communication equipment", "electronic gaming",
    "interactive media", "internet content",
]
POLICY_ACTOR_KEYWORDS = ["united states", "u.s.", "us", "us government", "china", "chinese", "beijing", "washington"]
POLICY_ACTION_KEYWORDS = [
    "policy", "subsidy", "subsidies", "funding", "tax credit", "export control", "export curb",
    "government plan", "industrial plan", "chips act", "award", "awards", "grant", "grants", "investment",
]
VIEW_SPEAKER_KEYWORDS = [
    "ceo", "chairman", "chief executive", "executive", "investor", "fund manager", "buffett", "dalio",
    "ackman", "druckenmiller", "howard marks", "cathie wood", "jamie dimon",
]
INVESTMENT_BANK_KEYWORDS = [
    "goldman sachs", "morgan stanley", "jpmorgan", "jp morgan", "bank of america", "bofa", "citi", "citigroup",
]
RULE_ACTION_KEYWORDS = ["rule", "rules", "regulation", "proposal", "standard", "guidance", "requirement", "filing"]
EXCHANGE_NAME_KEYWORDS = ["nyse", "nasdaq", "cboe", "stock exchange", "securities exchange"]
TRUSTED_NEWS_SOURCE_TERMS = [
    "reuters", "bloomberg", "cnbc", "associated press", "ap news", "wall street journal", "financial times",
    "barron's", "marketwatch", "business wire", "pr newswire", "globenewswire", "fortune", "forbes",
    "techcrunch", "the verge", "engadget", "investing.com", "yahoo finance", "morningstar",
    "msn", "business insider", "fox business", "nareit",
]

COLUMN_LABELS_BY_LANG = {
    LANG_EN: {
        "symbol": "Symbol",
        "last_date": "Date",
        "match_count": "Matches",
        "matched_traits": "Matched Traits",
        "close": "Close",
        "move_pct": "Move %",
        "gap_pct": "Gap %",
        "mover_ratio": "Mover Ratio",
        "turnover": "Turnover",
        "market_cap": "Market Cap",
        "box_width_pct": "Box Width %",
        "breakout_side": "Breakout",
        "ema5": "EMA5",
        "ema10": "EMA10",
        "ema20": "EMA20",
        "ema_bullish_days": "EMA Bull Days",
        "range_width_pct": "Range Width %",
        "range_days": "Range Days",
    },
    LANG_ZH: {
        "symbol": "代码",
        "last_date": "日期",
        "match_count": "命中数",
        "matched_traits": "命中特征",
        "close": "收盘价",
        "move_pct": "涨幅%",
        "gap_pct": "跳空%",
        "mover_ratio": "量比",
        "turnover": "成交额",
        "market_cap": "市值",
        "box_width_pct": "箱体宽度%",
        "breakout_side": "突破方向",
        "ema5": "EMA5",
        "ema10": "EMA10",
        "ema20": "EMA20",
        "ema_bullish_days": "EMA多头天数",
        "range_width_pct": "波动范围%",
        "range_days": "窄幅天数",
    },
}
COLUMN_LABELS = COLUMN_LABELS_BY_LANG[LANG_EN]

NEWS_COLUMN_LABELS_BY_LANG = {
    LANG_EN: {
        "symbol": "Symbol",
        "time": "Time",
        "category": "Category",
        "source": "Source",
        "headline": "Headline",
        "summary": "Main Idea / Summary",
    },
    LANG_ZH: {
        "symbol": "代码",
        "time": "时间",
        "category": "类别",
        "source": "来源",
        "headline": "标题",
        "summary": "主要内容 / 摘要",
    },
}

NEWS_CATEGORY_LABELS_BY_LANG = {
    LANG_EN: {
        NEWS_ALL: "All Categories",
        NEWS_TECH_COMPANY: "Tech Company Updates",
        NEWS_TECH_EVENTS: "Tech Events",
        NEWS_INDUSTRY_POLICY: "U.S./China Industry Policy",
        NEWS_GEOPOLITICS: "Geopolitics/Trade",
        NEWS_MARKET_VIEWS: "Executive/Investor Views",
        NEWS_BANK_RESEARCH: "Investment Bank Research",
        NEWS_SEC_RULES: "SEC Rules",
        NEWS_EXCHANGE_RULES: "Exchange Rules",
        NEWS_FED: "Federal Reserve",
        NEWS_HOT_TOPICS: "Investment Hot Topics",
    },
    LANG_ZH: {
        NEWS_ALL: "全部类别",
        NEWS_TECH_COMPANY: "科技公司动态",
        NEWS_TECH_EVENTS: "科技会议与展览",
        NEWS_INDUSTRY_POLICY: "中美产业政策",
        NEWS_GEOPOLITICS: "地缘政治与贸易",
        NEWS_MARKET_VIEWS: "高管与投资人观点",
        NEWS_BANK_RESEARCH: "投行行业研究",
        NEWS_SEC_RULES: "美国证监会新规",
        NEWS_EXCHANGE_RULES: "交易所新规",
        NEWS_FED: "美联储动态",
        NEWS_HOT_TOPICS: "投资界热议话题",
    },
}

SOURCE_UNIVERSE = "U.S. Stock Universe"
SOURCE_MANUAL = "Manual Symbols"

CHOICE_LABELS = {
    LANG_EN: {
        "source": {
            SOURCE_UNIVERSE: "U.S. Stock Universe",
            SOURCE_MANUAL: "Manual Symbols",
        },
        "match_mode": {
            MATCH_ANY: "Any Selected",
            MATCH_ALL: "All Selected",
        },
    },
    LANG_ZH: {
        "source": {
            SOURCE_UNIVERSE: "美股股票池",
            SOURCE_MANUAL: "手动输入代码",
        },
        "match_mode": {
            MATCH_ANY: "任意选中特征",
            MATCH_ALL: "全部选中特征",
        },
    },
}

UI_TEXT = {
    LANG_EN: {
        "window_title": "YFinance V3 Pattern Scanner",
        "app_title": "Stock Pattern Scanner",
        "app_subtitle": "yfinance V3",
        "section_universe": "Universe",
        "section_manual": "Manual Symbols",
        "section_thresholds": "V3 Thresholds",
        "section_traits": "Traits",
        "field_source": "Source",
        "field_period": "Period",
        "field_close_year": "Close Year",
        "field_close_month": "Close Month",
        "field_close_day": "Close Day",
        "field_max_symbols": "Max Symbols",
        "field_match_mode": "Match Mode",
        "field_mover_ratio": "Mover Ratio",
        "field_mover_turnover": "Mover Turnover",
        "field_min_move_pct": "Min Move %",
        "field_mover_market_cap": "Mover Market Cap",
        "field_min_price": "Min Price",
        "field_pattern_market_cap": "Pattern Market Cap",
        "field_daily_turnover": "Daily Turnover",
        "field_ema_bullish_days": "EMA Bullish Days",
        "field_range_days": "Range Days",
        "field_range_width_pct": "Range Width %",
        "field_box_days": "Box Days",
        "field_box_width_pct": "Box Width %",
        "field_breakout_turnover": "Breakout Turnover",
        "field_breakout_multiple": "Breakout Multiple",
        "allow_missing_market_cap": "Allow missing market cap",
        "button_scan": "Run Scan",
        "button_stop": "Stop",
        "button_export": "Export CSV",
        "button_language": "中文",
        "button_load_news": "Load News",
        "button_stop_news": "Stop News",
        "button_export_news": "Export News CSV",
        "button_open_news": "Open Article",
        "tab_results": "Results",
        "tab_news": "News",
        "results_title": "Results",
        "news_title": "News",
        "field_news_max_symbols": "Tech Symbols",
        "field_news_items": "Items / Search",
        "field_news_days": "News Range (Days)",
        "field_news_category": "Category",
        "count_matches": "{count} matches",
        "count_news": "{count} news items",
        "status_ready": "Ready to scan.",
        "news_status_ready": "Ready to load news.",
        "news_status_loading": "Loading {symbol} ({checked}/{total})...",
        "news_status_loading_tech_universe": "Loading verified U.S.-listed technology companies...",
        "news_status_done": "Done. {count} news items from {start_date} to {end_date}.",
        "news_status_stopping": "Stopping news load...",
        "news_status_translating": "Translating titles and summaries ({done}/{total})...",
        "summary_translating": "Translating...",
        "summary_translation_failed": "Translation unavailable: {text}",
        "status_preparing": "Preparing symbols...",
        "status_stopping": "Stopping after the current request...",
        "status_loading_universe": "Loading U.S. stock universe from NASDAQ Trader...",
        "status_downloading": "Downloading {start}-{end} of {total} from yfinance...",
        "status_checking": "Checking {symbol} ({checked}/{total})...",
        "status_error": "Error.",
        "status_done": "Done. {count} matches.",
        "dlg_missing_dep_title": "Missing dependency",
        "dlg_missing_dep_body": "Install first:\n\npython -m pip install yfinance pandas",
        "dlg_invalid_input_title": "Invalid input",
        "dlg_invalid_number_body": "Tech Symbols, Items / Search, and News Range must be whole numbers.",
        "dlg_invalid_date_body": "Choose both Close Month and Close Day, or leave both blank for today's date.",
        "dlg_no_symbols_title": "No symbols",
        "dlg_no_symbols_body": "Enter at least one ticker symbol.",
        "err_no_symbols_to_scan": "No symbols to scan.",
        "dlg_scan_failed_title": "Scan failed",
        "dlg_no_results_title": "No results",
        "dlg_no_results_body": "Run a scan first.",
        "dlg_no_news_symbols_title": "No symbols",
        "dlg_no_news_symbols_body": "Run a scan first or enter manual symbols.",
        "dlg_no_news_title": "No news",
        "dlg_no_news_body": "Load news first.",
        "dlg_no_news_link_title": "No article",
        "dlg_no_news_link_body": "Select a news row that has a source article.",
        "export_title": "Export yfinance prototype results",
        "news_export_title": "Export yfinance news results",
        "dlg_exported_title": "Exported",
        "dlg_exported_body": "Saved {count} rows.",
    },
    LANG_ZH: {
        "window_title": "YFinance V3 形态扫描器",
        "app_title": "股票形态扫描",
        "app_subtitle": "yfinance V3",
        "section_universe": "股票范围",
        "section_manual": "手动代码",
        "section_thresholds": "V3 参数",
        "section_traits": "技术特征",
        "field_source": "数据源",
        "field_period": "历史周期",
        "field_close_year": "收盘年份",
        "field_close_month": "收盘月份",
        "field_close_day": "收盘日期",
        "field_max_symbols": "最大股票数",
        "field_match_mode": "匹配方式",
        "field_mover_ratio": "量比",
        "field_mover_turnover": "放量成交额",
        "field_min_move_pct": "最低涨幅%",
        "field_mover_market_cap": "放量市值",
        "field_min_price": "最低股价",
        "field_pattern_market_cap": "形态市值",
        "field_daily_turnover": "单日成交额",
        "field_ema_bullish_days": "EMA多头天数",
        "field_range_days": "窄幅天数",
        "field_range_width_pct": "波动范围%",
        "field_box_days": "箱体天数",
        "field_box_width_pct": "箱体宽度%",
        "field_breakout_turnover": "突破成交额",
        "field_breakout_multiple": "突破放量倍数",
        "allow_missing_market_cap": "允许缺失市值",
        "button_scan": "开始扫描",
        "button_stop": "停止",
        "button_export": "导出CSV",
        "button_language": "English",
        "button_load_news": "加载新闻",
        "button_stop_news": "停止新闻",
        "button_export_news": "导出新闻CSV",
        "button_open_news": "打开原文",
        "tab_results": "扫描结果",
        "tab_news": "新闻",
        "results_title": "扫描结果",
        "news_title": "新闻",
        "field_news_max_symbols": "科技股数量",
        "field_news_items": "每次搜索条数",
        "field_news_days": "新闻范围（天）",
        "field_news_category": "新闻类别",
        "count_matches": "共 {count} 个结果",
        "count_news": "共 {count} 条新闻",
        "status_ready": "准备扫描。",
        "news_status_ready": "准备加载新闻。",
        "news_status_loading": "正在加载 {symbol} ({checked}/{total})...",
        "news_status_loading_tech_universe": "正在加载已验证的美国上市科技公司名单...",
        "news_status_done": "完成，{start_date} 至 {end_date} 共 {count} 条新闻。",
        "news_status_stopping": "正在停止新闻加载...",
        "news_status_translating": "正在翻译标题和摘要（{done}/{total}）...",
        "summary_translating": "正在翻译...",
        "summary_translation_failed": "翻译暂不可用：{text}",
        "status_preparing": "正在准备股票代码...",
        "status_stopping": "将在当前请求结束后停止...",
        "status_loading_universe": "正在从 NASDAQ Trader 加载美股股票池...",
        "status_downloading": "正在从 yfinance 下载 {start}-{end} / {total}...",
        "status_checking": "正在检查 {symbol} ({checked}/{total})...",
        "status_error": "出错。",
        "status_done": "完成，共 {count} 个结果。",
        "dlg_missing_dep_title": "缺少依赖",
        "dlg_missing_dep_body": "请先安装：\n\npython -m pip install yfinance pandas",
        "dlg_invalid_input_title": "输入无效",
        "dlg_invalid_number_body": "科技股数量、每次搜索条数和最近天数必须是整数。",
        "dlg_invalid_date_body": "请选择收盘月份和日期，或两项都留空使用今天日期。",
        "dlg_no_symbols_title": "没有股票代码",
        "dlg_no_symbols_body": "请至少输入一个股票代码。",
        "err_no_symbols_to_scan": "没有可扫描的股票代码。",
        "dlg_scan_failed_title": "扫描失败",
        "dlg_no_results_title": "没有结果",
        "dlg_no_results_body": "请先运行扫描。",
        "dlg_no_news_symbols_title": "没有股票代码",
        "dlg_no_news_symbols_body": "请先运行扫描，或输入手动股票代码。",
        "dlg_no_news_title": "没有新闻",
        "dlg_no_news_body": "请先加载新闻。",
        "dlg_no_news_link_title": "没有原文",
        "dlg_no_news_link_body": "请选择带有原文来源的新闻行。",
        "export_title": "导出 yfinance 扫描结果",
        "news_export_title": "导出 yfinance 新闻结果",
        "dlg_exported_title": "已导出",
        "dlg_exported_body": "已保存 {count} 行。",
    },
}

APP_BG = "#f5f5f7"
PANEL_BG = "#fbfbfd"
CARD_BG = "#ffffff"
FIELD_BG = "#ffffff"
BORDER = "#d2d2d7"
TEXT = "#1d1d1f"
MUTED = "#6e6e73"
SUBTLE = "#86868b"
ACCENT = "#0071e3"
ACCENT_DARK = "#005bb5"
GAIN = "#248a3d"
LOSS = "#d70015"

DEFAULT_SYMBOLS = """
AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, AMD, NFLX,
JPM, BAC, XOM, CVX, KO, PEP, COST, WMT, AAL, AA, ABT, AON,
ACA, ABM, ABG, ACHC, GFI, PLTR, SMCI, SOFI, RIVN
""".strip()

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
TODAY = date.today()
CURRENT_YEAR = TODAY.year
DEFAULT_MONTH = f"{TODAY.month:02d}"
DEFAULT_DAY = f"{TODAY.day:02d}"
MONTH_OPTIONS = [""] + [f"{month:02d}" for month in range(1, 13)]


def localized_text(lang: str, key: str, **kwargs) -> str:
    value = UI_TEXT.get(lang, UI_TEXT[LANG_EN]).get(key, UI_TEXT[LANG_EN].get(key, key))
    return value.format(**kwargs) if kwargs else value


def localized_trait(lang: str, key: str) -> str:
    return TRAIT_LABELS_BY_LANG.get(lang, TRAIT_LABELS_BY_LANG[LANG_EN]).get(key, key)


def localized_column(lang: str, key: str) -> str:
    return COLUMN_LABELS_BY_LANG.get(lang, COLUMN_LABELS_BY_LANG[LANG_EN]).get(key, key)


def localized_news_column(lang: str, key: str) -> str:
    return NEWS_COLUMN_LABELS_BY_LANG.get(lang, NEWS_COLUMN_LABELS_BY_LANG[LANG_EN]).get(key, key)


def localized_news_category(lang: str, key: str) -> str:
    return NEWS_CATEGORY_LABELS_BY_LANG.get(lang, NEWS_CATEGORY_LABELS_BY_LANG[LANG_EN]).get(key, key)


def localized_choice(lang: str, group: str, key: str) -> str:
    return CHOICE_LABELS.get(lang, CHOICE_LABELS[LANG_EN]).get(group, CHOICE_LABELS[LANG_EN][group]).get(key, key)


def choice_from_label(lang: str, group: str, label: str) -> str:
    labels = CHOICE_LABELS.get(lang, CHOICE_LABELS[LANG_EN]).get(group, {})
    for key, translated in labels.items():
        if translated == label:
            return key
    for key, translated in CHOICE_LABELS[LANG_EN].get(group, {}).items():
        if translated == label:
            return key
    return label


def localized_breakout_side(lang: str, value: str) -> str:
    if value == "Up":
        return "向上" if lang == LANG_ZH else "Up"
    return value


def day_options_for(year: int, month_text: str) -> list[str]:
    if not month_text:
        return [""]
    month = int(month_text)
    _, last_day = calendar.monthrange(year, month)
    return [""] + [f"{day:02d}" for day in range(1, last_day + 1)]


@dataclass
class ScannerConfig:
    source_mode: str
    symbols: list[str]
    period: str
    target_date: object | None
    selected_traits: set[str]
    match_mode: str
    max_symbols: int
    min_mover_ratio: float
    min_mover_turnover: float
    min_move_pct: float
    min_mover_market_cap: float
    min_price: float
    min_pattern_market_cap: float
    allow_missing_market_cap: bool
    min_daily_turnover: float
    ema_bullish_days: int
    range_days: int
    range_width_pct: float
    box_days: int
    box_width_pct: float
    min_breakout_turnover: float
    breakout_turnover_multiple: float


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_number(value) -> str:
    number = to_float(value)
    if abs(number) < 1e-12:
        return ""
    if abs(number) >= 1_000_000:
        return f"{number:,.0f}"
    if abs(number) >= 1_000:
        return f"{number:,.2f}"
    return f"{number:.4f}".rstrip("0").rstrip(".")


def parse_symbols(raw: str) -> list[str]:
    symbols: list[str] = []
    for part in raw.replace("\n", ",").replace(" ", ",").split(","):
        symbol = part.strip().upper()
        if not symbol:
            continue
        if symbol.startswith("US."):
            symbol = symbol[3:]
        symbol = symbol.replace(".", "-")
        symbols.append(symbol)
    return list(dict.fromkeys(symbols))


def yfinance_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def looks_like_common_stock(symbol: str, name: str) -> bool:
    lowered = name.lower()
    blocked_words = [
        " warrant",
        " warrants",
        " right",
        " rights",
        " unit",
        " units",
        " preferred",
        " preference",
        " notes due",
        " senior notes",
        " bond",
        " debenture",
        " etf",
        " fund",
        " trust preferred",
    ]
    if any(word in lowered for word in blocked_words):
        return False
    if symbol.endswith(("W", "WS", "WT", "U", "R")) and any(word in lowered for word in ["warrant", "unit", "right"]):
        return False
    return True


def load_symbol_directory() -> list[str]:
    symbols: list[str] = []

    with urllib.request.urlopen(NASDAQ_LISTED_URL, timeout=20) as response:
        text = response.read().decode("utf-8", errors="replace")
    for line in text.splitlines()[1:]:
        if not line or line.startswith("File Creation Time"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        symbol, name, _, test_issue, _, _, etf, _ = parts[:8]
        symbol = symbol.strip()
        if test_issue == "Y" or etf == "Y":
            continue
        if symbol and looks_like_common_stock(symbol, name):
            symbols.append(yfinance_symbol(symbol))

    with urllib.request.urlopen(OTHER_LISTED_URL, timeout=20) as response:
        text = response.read().decode("utf-8", errors="replace")
    for line in text.splitlines()[1:]:
        if not line or line.startswith("File Creation Time"):
            continue
        parts = line.split("|")
        if len(parts) < 7:
            continue
        symbol, name, _, _, etf, _, test_issue = parts[:7]
        symbol = symbol.strip()
        if test_issue == "Y" or etf == "Y":
            continue
        if symbol and looks_like_common_stock(symbol, name):
            symbols.append(yfinance_symbol(symbol))

    return list(dict.fromkeys(symbols))


def chunks(items: list[str], size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def normalize_history(data):
    if pd is None or data is None or getattr(data, "empty", True):
        return None

    daily = data.copy()
    daily.columns = [str(column).title() for column in daily.columns]
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(column not in daily.columns for column in required):
        return None

    daily = daily[required].dropna(subset=["Close", "High", "Low"])
    if daily.empty:
        return None

    for column in required:
        daily[column] = daily[column].apply(to_float)
    daily = daily[daily["Close"] > 0]
    if daily.empty:
        return None

    daily["Turnover"] = daily["Close"] * daily["Volume"]
    for span in [5, 10, 20, 50, 200]:
        daily[f"EMA{span}"] = daily["Close"].ewm(span=span, adjust=False).mean()
    return daily


def history_as_of_date(daily, target_date):
    if daily is None or target_date is None:
        return daily
    target = pd.Timestamp(target_date)
    if getattr(target, "tzinfo", None) is not None:
        target = target.tz_localize(None)
    dates = pd.to_datetime(daily.index)
    if getattr(dates, "tz", None) is not None:
        dates = dates.tz_localize(None)
    return daily.loc[dates.normalize() <= target.normalize()]


def contains_news_keyword(text: str, keyword: str) -> bool:
    lowered = text.lower()
    keyword = keyword.lower()
    if re.fullmatch(r"[a-z0-9]+", keyword):
        return re.search(rf"\b{re.escape(keyword)}\b", lowered) is not None
    return keyword in lowered


def matches_news_category(text: str, category: str) -> bool:
    if category == NEWS_TECH_COMPANY:
        has_product_launch = any(contains_news_keyword(text, keyword) for keyword in TECH_EVENT_KEYWORDS)
        has_newness = any(contains_news_keyword(text, keyword) for keyword in TECH_NEWNESS_KEYWORDS)
        has_tech_product = any(contains_news_keyword(text, keyword) for keyword in TECH_PRODUCT_KEYWORDS)
        has_announcement = any(contains_news_keyword(text, keyword) for keyword in TECH_ANNOUNCE_KEYWORDS)
        has_role = any(contains_news_keyword(text, keyword) for keyword in EXECUTIVE_ROLE_KEYWORDS)
        has_buy = any(contains_news_keyword(text, keyword) for keyword in EXECUTIVE_BUY_KEYWORDS)
        has_business_model = any(contains_news_keyword(text, keyword) for keyword in BUSINESS_MODEL_KEYWORDS)
        return (
            has_product_launch
            or ((has_newness or has_announcement) and has_tech_product)
            or (has_role and has_buy)
            or has_business_model
        )
    if category == NEWS_INDUSTRY_POLICY:
        has_actor = any(contains_news_keyword(text, keyword) for keyword in POLICY_ACTOR_KEYWORDS)
        has_action = any(contains_news_keyword(text, keyword) for keyword in POLICY_ACTION_KEYWORDS)
        return has_actor and has_action
    if category == NEWS_MARKET_VIEWS:
        has_speaker = any(contains_news_keyword(text, keyword) for keyword in VIEW_SPEAKER_KEYWORDS)
        has_view = any(contains_news_keyword(text, keyword) for keyword in NEWS_CATEGORY_KEYWORDS[NEWS_MARKET_VIEWS])
        return has_speaker and has_view
    if category == NEWS_BANK_RESEARCH:
        has_bank = any(contains_news_keyword(text, keyword) for keyword in INVESTMENT_BANK_KEYWORDS)
        has_research = any(contains_news_keyword(text, keyword) for keyword in NEWS_CATEGORY_KEYWORDS[NEWS_BANK_RESEARCH])
        return has_bank and has_research
    if category == NEWS_SEC_RULES:
        has_sec = contains_news_keyword(text, "sec") or contains_news_keyword(text, "securities and exchange commission")
        has_rule = any(contains_news_keyword(text, keyword) for keyword in RULE_ACTION_KEYWORDS)
        return has_sec and has_rule
    if category == NEWS_EXCHANGE_RULES:
        has_exchange = any(contains_news_keyword(text, keyword) for keyword in EXCHANGE_NAME_KEYWORDS)
        has_rule = any(contains_news_keyword(text, keyword) for keyword in RULE_ACTION_KEYWORDS)
        return has_exchange and has_rule
    if category == NEWS_HOT_TOPICS:
        return True
    return any(contains_news_keyword(text, keyword) for keyword in NEWS_CATEGORY_KEYWORDS.get(category, []))


def classify_news(text: str) -> str:
    priority = [
        NEWS_SEC_RULES,
        NEWS_EXCHANGE_RULES,
        NEWS_FED,
        NEWS_GEOPOLITICS,
        NEWS_INDUSTRY_POLICY,
        NEWS_TECH_EVENTS,
        NEWS_BANK_RESEARCH,
        NEWS_MARKET_VIEWS,
        NEWS_TECH_COMPANY,
    ]
    for category in priority:
        if matches_news_category(text, category):
            return category
    return NEWS_HOT_TOPICS


def news_timestamp(value) -> float:
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return 0.0


def format_news_time(value) -> str:
    timestamp = news_timestamp(value)
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def news_main_idea(title: str, summary: str, max_length: int = 320) -> str:
    text = summary.strip() or title.strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    shortened = text[: max_length - 3].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{shortened}..."


def parse_translation_response(payload) -> str:
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        return ""
    parts = []
    for segment in payload[0]:
        if isinstance(segment, list) and segment and isinstance(segment[0], str):
            parts.append(segment[0])
    return "".join(parts).strip()


def translate_summary_to_chinese(text: str) -> str:
    if not text.strip():
        return ""
    query = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "auto",
            "tl": "zh-CN",
            "dt": "t",
            "q": text,
        }
    )
    request = urllib.request.Request(
        f"{SUMMARY_TRANSLATE_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return ""
    return parse_translation_response(payload)


def clean_rss_text(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", text).strip()


def news_source_rank(source: str, official_hint: str = "", source_url: str = "") -> int:
    source_text = source.lower().strip()
    hint_text = official_hint.lower().strip()
    if hint_text and source_text and (source_text in hint_text or hint_text in source_text):
        return 4
    if ".gov" in source_url.lower() or any(
        term in source_text for term in ["securities and exchange commission", "federal reserve"]
    ):
        return 4
    if any(term in source_text for term in TRUSTED_NEWS_SOURCE_TERMS):
        return 3
    return 1


def concise_company_name(value: str) -> str:
    name = value.strip()
    return re.sub(
        r",?\s+(inc\.?|incorporated|corporation|corp\.?|company|co\.?|ltd\.?|plc)$",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip() or name


def build_us_technology_aliases(quotes: list[dict]) -> list[tuple[str, str, str]]:
    generic_first_words = {
        "advanced", "american", "digital", "global", "international", "national", "the", "united",
    }
    candidates: dict[str, dict[str, str]] = {}
    for quote in quotes:
        symbol = str(quote.get("symbol", "")).upper().strip()
        name = str(
            quote.get("longName")
            or quote.get("longname")
            or quote.get("shortName")
            or quote.get("shortname")
            or ""
        ).strip()
        if not symbol or not name:
            continue
        base_name = concise_company_name(name)
        aliases = {base_name}
        first_word = re.split(r"\s+", base_name)[0].strip(".,")
        if len(first_word) >= 4 and first_word.lower() not in generic_first_words:
            aliases.add(first_word)
        for alias in aliases:
            key = alias.lower()
            candidates.setdefault(key, {})[symbol] = name
    aliases: list[tuple[str, str, str]] = []
    for alias, owners in candidates.items():
        if len(owners) != 1:
            continue
        symbol, name = next(iter(owners.items()))
        aliases.append((alias, symbol, name))
    aliases.sort(key=lambda item: len(item[0]), reverse=True)
    return aliases


def load_us_listed_technology_aliases(force_refresh: bool = False) -> list[tuple[str, str, str]]:
    global _US_TECH_COMPANY_ALIASES
    if _US_TECH_COMPANY_ALIASES is not None and not force_refresh:
        return list(_US_TECH_COMPANY_ALIASES)
    if yf is None or not hasattr(yf, "screen") or not hasattr(yf, "EquityQuery"):
        return []
    try:
        query = yf.EquityQuery(
            "and",
            [
                yf.EquityQuery("is-in", ["exchange", *sorted(US_PRIMARY_EQUITY_EXCHANGES)]),
                yf.EquityQuery(
                    "or",
                    [
                        yf.EquityQuery("eq", ["sector", "Technology"]),
                        yf.EquityQuery(
                            "is-in",
                            ["industry", "Electronic Gaming & Multimedia", "Internet Content & Information"],
                        ),
                    ],
                ),
            ],
        )
        first_page = yf.screen(query, offset=0, size=250, sortField="ticker", sortAsc=True)
        total = int(first_page.get("total", 0) or 0)
        quotes = list(first_page.get("quotes", []))
        for offset in range(250, total, 250):
            page = yf.screen(query, offset=offset, size=250, sortField="ticker", sortAsc=True)
            quotes.extend(page.get("quotes", []))
    except Exception:
        return []
    _US_TECH_COMPANY_ALIASES = build_us_technology_aliases(quotes)
    return list(_US_TECH_COMPANY_ALIASES)


def match_us_listed_technology_company(
    headline: str,
    aliases: list[tuple[str, str, str]],
) -> tuple[str, str] | None:
    matches: list[tuple[int, int, str, str]] = []
    for alias, symbol, name in aliases:
        alias_match = re.search(rf"\b{re.escape(alias)}\b", headline, re.IGNORECASE)
        symbol_match = re.search(rf"\({re.escape(symbol)}\)", headline, re.IGNORECASE)
        positions = [match.start() for match in [alias_match, symbol_match] if match is not None]
        if positions:
            matches.append((min(positions), -len(alias), symbol, name))
    if not matches:
        return None
    _, _, symbol, name = min(matches)
    return symbol, name


def google_news_timestamp(value: str) -> float:
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError, OverflowError):
        return 0.0


def google_news_row(item, category: str, symbol: str, official_hint: str = "") -> dict:
    source_node = item.find("source")
    source = clean_rss_text(source_node.text if source_node is not None and source_node.text else "")
    source_url = source_node.get("url", "") if source_node is not None else ""
    title = clean_rss_text(item.findtext("title") or "")
    suffix = f" - {source}"
    if source and title.lower().endswith(suffix.lower()):
        title = title[: -len(suffix)].strip()
    description = clean_rss_text(item.findtext("description") or "")
    if title and title.lower() in description.lower():
        description = ""
    published = item.findtext("pubDate") or ""
    published_ts = google_news_timestamp(published)
    source_rank = news_source_rank(source, official_hint, source_url)
    if source and len(source) >= 4 and contains_news_keyword(title, source):
        source_rank = max(source_rank, 4)
    return {
        "symbol": symbol,
        "time": format_news_time(published_ts),
        "category": category,
        "source": source,
        "headline": title or "(no headline)",
        "summary": news_main_idea(title or "(no headline)", description),
        "link": item.findtext("link") or "",
        "_published_ts": published_ts,
        "_news_id": item.findtext("guid") or "",
        "_search_text": f"{title} {description}".strip(),
        "_source_rank": source_rank,
        "_source_url": source_url,
    }


def fetch_google_news_rss(
    query: str,
    category: str,
    limit: int,
    recent_days: int,
    symbol: str = "MARKET",
    official_hint: str = "",
    required_text: str = "",
    company_aliases: list[tuple[str, str, str]] | None = None,
) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    request = urllib.request.Request(
        f"{GOOGLE_NEWS_RSS_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())
    except Exception:
        return []
    rows: list[dict] = []
    for item in root.findall(".//item"):
        row = google_news_row(item, category, symbol, official_hint)
        if company_aliases is not None:
            matched_company = match_us_listed_technology_company(str(row.get("headline", "")), company_aliases)
            if matched_company is None:
                continue
            matched_symbol, matched_name = matched_company
            row["symbol"] = matched_symbol
            row["_source_rank"] = max(
                to_float(row.get("_source_rank")),
                news_source_rank(
                    str(row.get("source", "")),
                    matched_name,
                    str(row.get("_source_url", "")),
                ),
            )
        if required_text and not contains_news_keyword(str(row.get("headline", "")), required_text):
            continue
        if not matches_news_category(row.get("_search_text", ""), category):
            continue
        if not is_recent_news(row, recent_days):
            continue
        rows.append(row)
    return sorted(
        rows,
        key=lambda item: (to_float(item.get("_published_ts")), to_float(item.get("_source_rank"))),
        reverse=True,
    )[:limit]


def extract_news_row(symbol: str, item: dict, category: str | None = None) -> dict:
    content = item.get("content") if isinstance(item, dict) else None
    if isinstance(content, dict):
        title = content.get("title") or ""
        summary = content.get("summary") or ""
        provider = content.get("provider") or {}
        source = provider.get("displayName") if isinstance(provider, dict) else str(provider)
        link_data = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        link = link_data.get("url") if isinstance(link_data, dict) else str(link_data or "")
        published = content.get("pubDate") or content.get("displayTime")
    else:
        title = item.get("title", "") if isinstance(item, dict) else ""
        summary = item.get("summary", "") if isinstance(item, dict) else ""
        source = item.get("publisher", "") if isinstance(item, dict) else ""
        link = item.get("link", "") if isinstance(item, dict) else ""
        published = item.get("providerPublishTime") if isinstance(item, dict) else ""
    headline = title or summary or "(no headline)"
    text = f"{title} {summary}".strip()
    return {
        "symbol": symbol,
        "time": format_news_time(published),
        "category": category or classify_news(text),
        "source": source or "",
        "headline": headline,
        "summary": news_main_idea(headline, summary),
        "link": link or "",
        "_published_ts": news_timestamp(published),
        "_news_id": item.get("uuid", "") if isinstance(item, dict) else "",
        "_search_text": text,
        "_source_rank": news_source_rank(source or ""),
    }


def news_date_range(recent_days: int, today: date | None = None) -> tuple[date, date]:
    day_count = max(1, recent_days)
    end_date = today or datetime.now().astimezone().date()
    start_date = end_date - timedelta(days=day_count - 1)
    return start_date, end_date


def is_recent_news(row: dict, recent_days: int) -> bool:
    published = to_float(row.get("_published_ts"))
    if not published:
        return True
    start_date, end_date = news_date_range(recent_days)
    published_date = datetime.fromtimestamp(published, tz=timezone.utc).astimezone().date()
    return start_date <= published_date <= end_date


def is_technology_quote(quote: dict) -> bool:
    sector = str(quote.get("sector") or quote.get("sectorDisp") or "").lower()
    industry = str(quote.get("industry") or quote.get("industryDisp") or "").lower()
    return sector == "technology" or any(contains_news_keyword(industry, keyword) for keyword in TECH_INDUSTRY_KEYWORDS)


def is_us_listed_technology_quote(quote: dict) -> bool:
    exchange = str(quote.get("exchange", "")).upper()
    return exchange in US_PRIMARY_EQUITY_EXCHANGES and is_technology_quote(quote)


def yahoo_news_search(query: str, limit: int):
    if yf is None:
        return None
    try:
        return yf.Search(
            query,
            max_results=5,
            news_count=max(1, limit),
            lists_count=0,
            include_cb=False,
            recommended=0,
            timeout=20,
            raise_errors=False,
        )
    except Exception:
        return None


def fetch_technology_company_news(symbol: str, limit: int, recent_days: int) -> list[dict]:
    search = yahoo_news_search(symbol, max(limit * 3, 10))
    if search is None:
        return []
    exact_quote = next(
        (quote for quote in search.quotes if str(quote.get("symbol", "")).upper() == symbol.upper()),
        None,
    )
    if not exact_quote or not is_us_listed_technology_quote(exact_quote):
        return []
    company_name = str(exact_quote.get("longname") or exact_quote.get("shortname") or symbol)
    search_name = concise_company_name(company_name)
    rows: list[dict] = []
    for item in search.news:
        related = [str(value).upper() for value in item.get("relatedTickers", [])] if isinstance(item, dict) else []
        if related and symbol.upper() not in related:
            continue
        row = extract_news_row(symbol, item, NEWS_TECH_COMPANY)
        row["_source_rank"] = news_source_rank(str(row.get("source", "")), company_name)
        if matches_news_category(row.get("_search_text", ""), NEWS_TECH_COMPANY) and is_recent_news(row, recent_days):
            rows.append(row)
    google_query = (
        f'\"{search_name}\" '
        f'(launches OR unveils OR introduces OR \"now available\" OR appoints OR buyback OR update OR new) '
        f'when:{recent_days}d'
    )
    rows.extend(
        fetch_google_news_rss(
            google_query,
            NEWS_TECH_COMPANY,
            max(limit * 3, 15),
            recent_days,
            symbol=symbol,
            official_hint=company_name,
            required_text=search_name,
        )
    )
    ranked = sorted(
        deduplicate_news(rows),
        key=lambda item: (to_float(item.get("_source_rank")), to_float(item.get("_published_ts"))),
        reverse=True,
    )
    return ranked[:limit]


def fetch_topic_news(category: str, query: str, limit: int, recent_days: int) -> list[dict]:
    search = yahoo_news_search(query, max(limit * 2, limit))
    rows: list[dict] = []
    required_entity = re.sub(r"\s+investor$", "", query, flags=re.IGNORECASE).strip()
    if search is not None:
        for item in search.news:
            related = item.get("relatedTickers", []) if isinstance(item, dict) else []
            scope = ",".join(str(value).upper() for value in related[:3]) or "MARKET"
            row = extract_news_row(scope, item, category)
            if category in {NEWS_MARKET_VIEWS, NEWS_BANK_RESEARCH} and not contains_news_keyword(
                row.get("_search_text", ""),
                required_entity,
            ):
                continue
            if matches_news_category(row.get("_search_text", ""), category) and is_recent_news(row, recent_days):
                rows.append(row)
    google_query = ""
    if category == NEWS_MARKET_VIEWS:
        google_query = f'\"{query}\" (interview OR says OR warns OR outlook OR views OR letter) when:{recent_days}d'
    elif category == NEWS_BANK_RESEARCH:
        google_query = (
            f'\"{query}\" (research OR outlook OR forecast OR favors OR recommends OR upgrades OR downgrades) '
            f'when:{recent_days}d'
        )
    if google_query:
        rows.extend(
            fetch_google_news_rss(
                google_query,
                category,
                max(limit * 3, 15),
                recent_days,
                official_hint=query,
                required_text=required_entity,
            )
        )
    ranked = sorted(
        deduplicate_news(rows),
        key=lambda item: (to_float(item.get("_source_rank")), to_float(item.get("_published_ts"))),
        reverse=True,
    )
    return ranked[:limit]


NEWS_DEDUPE_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "its", "of", "on", "the", "to", "with",
    "stock", "shares", "company", "corporation", "inc", "is", "needs", "new", "now", "so", "stricter", "welcome",
}


def normalized_news_event_text(headline: str) -> str:
    text = headline.lower()
    replacements = [
        (r"\b(launches|launched|launch|rolls out|rolled out|introduces|introduced|unveils|unveiled|releases|released)\b", " launch "),
        (r"\b(rollout|now available|now globally available|globally available|available worldwide)\b", " launch global "),
        (r"\b(age-based|age-gated)\b", " age "),
        (r"\b(kids|children|child|teens|minor users|younger users|under 16s?)\b", " youth "),
        (r"\b(protect|protection|safety features|safety controls|parental controls|controls)\b", " safety "),
        (r"\b(accounts|account tiers|tiers)\b", " account "),
        (r"\b(globally|global|worldwide)\b", " global "),
        (r"\b(buys shares|bought shares|purchases shares|increases stake|boosts stake)\b", " insiderbuy "),
        (r"\b(business model|subscription model|advertising model|licensing model|monetization model)\b", " businessmodel "),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    tokens = [token for token in re.findall(r"[a-z0-9]+", text) if token not in NEWS_DEDUPE_STOPWORDS]
    return " ".join(tokens)


def same_news_event(first: dict, second: dict) -> bool:
    if first.get("category") != second.get("category"):
        return False
    first_symbol = str(first.get("symbol", ""))
    second_symbol = str(second.get("symbol", ""))
    if first_symbol not in {"", "MARKET"} and second_symbol not in {"", "MARKET"} and first_symbol != second_symbol:
        return False
    first_time = to_float(first.get("_published_ts"))
    second_time = to_float(second.get("_published_ts"))
    if first_time and second_time and abs(first_time - second_time) > 96 * 3600:
        return False
    first_text = normalized_news_event_text(str(first.get("headline", "")))
    second_text = normalized_news_event_text(str(second.get("headline", "")))
    if not first_text or not second_text:
        return False
    if first_text == second_text:
        return True
    first_tokens = set(first_text.split())
    second_tokens = set(second_text.split())
    overlap = len(first_tokens & second_tokens) / max(1, len(first_tokens | second_tokens))
    sequence = SequenceMatcher(None, first_text, second_text).ratio()
    threshold = 0.35 if first_symbol == second_symbol and first_symbol not in {"", "MARKET"} else 0.5
    return overlap >= threshold or sequence >= (0.62 if threshold == 0.35 else 0.72)


def deduplicate_news(rows: list[dict]) -> list[dict]:
    preferred = sorted(
        rows,
        key=lambda item: (to_float(item.get("_source_rank")), to_float(item.get("_published_ts"))),
        reverse=True,
    )
    unique: list[dict] = []
    for row in preferred:
        if any(same_news_event(row, existing) for existing in unique):
            continue
        unique.append(row)
    return sorted(
        unique,
        key=lambda item: (to_float(item.get("_published_ts")), to_float(item.get("_source_rank"))),
        reverse=True,
    )


def get_symbol_frame(raw, symbol: str, symbol_count: int):
    if raw is None or getattr(raw, "empty", True):
        return None
    if not isinstance(raw.columns, pd.MultiIndex):
        return raw if symbol_count == 1 else None
    if symbol in raw.columns.get_level_values(0):
        return raw[symbol]
    upper_lookup = {str(name).upper(): name for name in raw.columns.get_level_values(0)}
    actual = upper_lookup.get(symbol.upper())
    if actual is not None:
        return raw[actual]
    return None


def recent_turnover_floor_ok(daily, days: int, min_turnover: float) -> bool:
    if min_turnover <= 0:
        return True
    if daily is None or len(daily) < days:
        return False
    return bool((daily.tail(days)["Turnover"].apply(to_float) >= min_turnover).all())


def market_cap_ok_value(market_cap: float, threshold: float, allow_missing: bool) -> bool:
    if market_cap <= 0:
        return allow_missing
    return market_cap >= threshold


def ema_bullish_5_10_20(row) -> bool:
    return to_float(row.get("EMA5")) >= to_float(row.get("EMA10")) >= to_float(row.get("EMA20")) > 0


def ema_bullish_run_days(daily) -> int:
    days = 0
    for _, row in daily.iloc[::-1].iterrows():
        if not ema_bullish_5_10_20(row):
            break
        days += 1
    return days


def range_width_for_days(daily, days: int) -> float:
    if daily is None or len(daily) < days:
        return float("inf")
    recent = daily.tail(days)
    high = to_float(recent["High"].max())
    low = to_float(recent["Low"].min())
    if high <= 0 or low <= 0:
        return float("inf")
    return (high / low - 1) * 100


def compute_market_cap(symbol: str) -> float:
    if yf is None:
        return 0.0
    try:
        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None)
        if fast_info is not None:
            for key in ["market_cap", "marketCap"]:
                try:
                    market_cap = fast_info.get(key)
                    if market_cap:
                        return to_float(market_cap)
                except Exception:
                    pass
            try:
                shares = to_float(fast_info.get("shares"))
                last_price = to_float(fast_info.get("lastPrice"))
                if shares > 0 and last_price > 0:
                    return shares * last_price
            except Exception:
                pass
    except Exception:
        return 0.0
    return 0.0


def base_row(symbol: str, daily, market_cap: float) -> dict:
    latest = daily.iloc[-1]
    previous = daily.iloc[-2] if len(daily) >= 2 else latest
    previous_20 = daily.iloc[-21:-1] if len(daily) >= 21 else daily.iloc[:-1]
    close = to_float(latest.get("Close"))
    prev_close = to_float(previous.get("Close"))
    open_price = to_float(latest.get("Open"))
    turnover = to_float(latest.get("Turnover"))
    avg_volume_20 = to_float(previous_20["Volume"].mean()) if not previous_20.empty else 0
    mover_ratio = to_float(latest.get("Volume")) / avg_volume_20 if avg_volume_20 > 0 else 0
    move_pct = (close - prev_close) / prev_close * 100 if close > 0 and prev_close > 0 else 0
    gap_pct = (open_price - prev_close) / prev_close * 100 if open_price > 0 and prev_close > 0 else 0

    return {
        "symbol": symbol,
        "last_date": str(daily.index[-1].date()) if hasattr(daily.index[-1], "date") else str(daily.index[-1]),
        "match_count": 0,
        "matched_traits": "",
        "close": close,
        "move_pct": move_pct,
        "gap_pct": gap_pct,
        "mover_ratio": mover_ratio,
        "turnover": turnover,
        "market_cap": market_cap,
        "box_width_pct": "",
        "breakout_side": "",
        "ema5": to_float(latest.get("EMA5")),
        "ema10": to_float(latest.get("EMA10")),
        "ema20": to_float(latest.get("EMA20")),
        "ema_bullish_days": "",
        "range_width_pct": "",
        "range_days": "",
        "_matched_trait_keys": [],
    }


def add_traits(row: dict, daily, config: ScannerConfig) -> dict:
    matched: list[str] = []
    latest = daily.iloc[-1]
    close = to_float(latest.get("Close"))
    turnover = to_float(latest.get("Turnover"))
    market_cap_loaded = to_float(row.get("market_cap")) > 0

    def load_market_cap() -> float:
        nonlocal market_cap_loaded
        if not market_cap_loaded:
            row["market_cap"] = compute_market_cap(str(row.get("symbol", "")))
            market_cap_loaded = True
        return to_float(row.get("market_cap"))

    def market_cap_ok(threshold: float) -> bool:
        return market_cap_ok_value(load_market_cap(), threshold, config.allow_missing_market_cap)

    if TRAIT_MOVER in config.selected_traits:
        if (
            close >= config.min_price
            and to_float(row.get("move_pct")) >= config.min_move_pct
            and to_float(row.get("mover_ratio")) >= config.min_mover_ratio
            and turnover >= config.min_mover_turnover
            and market_cap_ok(config.min_mover_market_cap)
        ):
            matched.append(TRAIT_MOVER)

    ema_bullish_days = ema_bullish_run_days(daily)
    row["ema_bullish_days"] = ema_bullish_days
    if TRAIT_EMA_BULLISH in config.selected_traits:
        if (
            close >= config.min_price
            and ema_bullish_days >= config.ema_bullish_days
            and recent_turnover_floor_ok(daily, config.ema_bullish_days, config.min_daily_turnover)
            and market_cap_ok(config.min_pattern_market_cap)
        ):
            matched.append(TRAIT_EMA_BULLISH)

    range_width_pct = range_width_for_days(daily, config.range_days)
    row["range_width_pct"] = range_width_pct
    row["range_days"] = config.range_days if range_width_pct != float("inf") else ""
    if TRAIT_TIGHT_RANGE in config.selected_traits:
        if (
            close >= config.min_price
            and range_width_pct <= config.range_width_pct
            and recent_turnover_floor_ok(daily, config.range_days, config.min_daily_turnover)
            and market_cap_ok(config.min_pattern_market_cap)
        ):
            matched.append(TRAIT_TIGHT_RANGE)

    if TRAIT_BOX_BREAKOUT in config.selected_traits and len(daily) >= config.box_days:
        box_window = daily.tail(config.box_days)
        setup_box = box_window.iloc[:-1]
        box_high = to_float(box_window["High"].max())
        box_low = to_float(box_window["Low"].min())
        breakout_level = to_float(setup_box["High"].max()) if not setup_box.empty else 0
        box_width_pct = (box_high / box_low - 1) * 100 if box_high > 0 and box_low > 0 else float("inf")
        row["box_width_pct"] = box_width_pct
        previous_five = daily.iloc[-6:-1] if len(daily) >= 6 else daily.iloc[:-1]
        avg_turnover_5 = to_float(previous_five["Turnover"].mean()) if not previous_five.empty else 0
        if close > breakout_level:
            row["breakout_side"] = "Up"
        if (
            row.get("breakout_side") == "Up"
            and box_width_pct <= config.box_width_pct
            and avg_turnover_5 > 0
            and turnover >= avg_turnover_5 * config.breakout_turnover_multiple
            and turnover >= config.min_breakout_turnover
            and market_cap_ok(config.min_pattern_market_cap)
        ):
            matched.append(TRAIT_BOX_BREAKOUT)

    selected_count = len(config.selected_traits)
    row["_matched_trait_keys"] = [key for key in TRAIT_LABELS if key in matched]
    row["match_count"] = len(row["_matched_trait_keys"])
    row["matched_traits"] = ", ".join(TRAIT_LABELS[key] for key in row["_matched_trait_keys"])
    if selected_count == 0:
        row["_trait_pass"] = True
    elif config.match_mode == MATCH_ALL:
        row["_trait_pass"] = row["match_count"] == selected_count
    else:
        row["_trait_pass"] = row["match_count"] > 0
    return row


class YFinancePrototypeScanner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("YFinance V3 Pattern Scanner")
        self.geometry("1480x900")
        self.minsize(1200, 740)
        self.configure(bg=APP_BG)

        self.results: list[dict] = []
        self.news_results: list[dict] = []
        self.news_item_links: dict[str, str] = {}
        self.summary_translations: dict[str, str] = {}
        self.summary_translation_failures: set[str] = set()
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.news_stop_event = threading.Event()
        self.summary_translation_stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.news_worker: threading.Thread | None = None
        self.summary_translation_worker: threading.Thread | None = None
        self.lang = LANG_EN
        self.label_widgets: dict[str, ttk.Label] = {}
        self.button_widgets: dict[str, ttk.Button] = {}
        self.trait_widgets: dict[str, ttk.Checkbutton] = {}

        self.source_mode_var = tk.StringVar(value=SOURCE_UNIVERSE)
        self.source_display_var = tk.StringVar(value=localized_choice(self.lang, "source", SOURCE_UNIVERSE))
        self.symbols_var = tk.StringVar(value=DEFAULT_SYMBOLS)
        self.period_var = tk.StringVar(value="2y")
        self.close_year_var = tk.StringVar(value=str(CURRENT_YEAR))
        self.close_month_var = tk.StringVar(value=DEFAULT_MONTH)
        self.close_day_var = tk.StringVar(value=DEFAULT_DAY)
        self.max_symbols_var = tk.StringVar(value="0")
        self.match_mode_var = tk.StringVar(value=MATCH_ANY)
        self.match_mode_display_var = tk.StringVar(value=localized_choice(self.lang, "match_mode", MATCH_ANY))
        self.min_mover_ratio_var = tk.StringVar(value="2")
        self.min_mover_turnover_var = tk.StringVar(value="50000000")
        self.min_move_pct_var = tk.StringVar(value="10")
        self.min_mover_market_cap_var = tk.StringVar(value="100000000")
        self.min_price_var = tk.StringVar(value="3")
        self.min_pattern_market_cap_var = tk.StringVar(value="500000000")
        self.allow_missing_market_cap_var = tk.BooleanVar(value=False)
        self.min_daily_turnover_var = tk.StringVar(value="20000000")
        self.ema_bullish_days_var = tk.StringVar(value="5")
        self.range_days_var = tk.StringVar(value="3")
        self.range_width_pct_var = tk.StringVar(value="5")
        self.box_days_var = tk.StringVar(value="20")
        self.box_width_pct_var = tk.StringVar(value="15")
        self.min_breakout_turnover_var = tk.StringVar(value="30000000")
        self.breakout_turnover_multiple_var = tk.StringVar(value="1.5")
        self.news_max_symbols_var = tk.StringVar(value="25")
        self.news_items_per_symbol_var = tk.StringVar(value="10")
        self.news_recent_days_var = tk.StringVar(value="5")
        self.news_range_start, self.news_range_end = news_date_range(5)
        self.news_filter_key = NEWS_ALL
        self.news_filter_display_var = tk.StringVar(value=localized_news_category(self.lang, NEWS_ALL))

        self.trait_vars = {
            TRAIT_MOVER: tk.BooleanVar(value=True),
            TRAIT_EMA_BULLISH: tk.BooleanVar(value=True),
            TRAIT_TIGHT_RANGE: tk.BooleanVar(value=True),
            TRAIT_BOX_BREAKOUT: tk.BooleanVar(value=True),
        }

        self._configure_styles()
        self._build_layout()
        self._apply_language()
        self.after(100, self._poll_messages)

    def _t(self, key: str, **kwargs) -> str:
        return localized_text(self.lang, key, **kwargs)

    def _choice_values(self, group: str) -> list[str]:
        labels = CHOICE_LABELS.get(self.lang, CHOICE_LABELS[LANG_EN]).get(group, {})
        return list(labels.values())

    def _sync_choice_displays(self) -> None:
        self.source_display_var.set(localized_choice(self.lang, "source", self.source_mode_var.get()))
        self.match_mode_display_var.set(localized_choice(self.lang, "match_mode", self.match_mode_var.get()))

    def _on_source_selected(self, _event=None) -> None:
        self.source_mode_var.set(choice_from_label(self.lang, "source", self.source_display_var.get()))

    def _on_match_mode_selected(self, _event=None) -> None:
        self.match_mode_var.set(choice_from_label(self.lang, "match_mode", self.match_mode_display_var.get()))

    def _news_category_values(self) -> list[str]:
        return [localized_news_category(self.lang, key) for key in [NEWS_ALL, *NEWS_CATEGORY_ORDER]]

    def _on_news_category_selected(self, _event=None) -> None:
        selected = self.news_filter_display_var.get()
        for key in [NEWS_ALL, *NEWS_CATEGORY_ORDER]:
            if selected in {localized_news_category(self.lang, key), localized_news_category(LANG_EN, key)}:
                self.news_filter_key = key
                break
        self.refresh_news_table()
        self.start_summary_translation()

    def _on_close_month_selected(self, _event=None) -> None:
        self._refresh_close_day_options()

    def _refresh_close_day_options(self) -> None:
        if not hasattr(self, "close_day_combo"):
            return
        year = int(self.close_year_var.get())
        values = day_options_for(year, self.close_month_var.get())
        if self.close_day_var.get() not in values:
            self.close_day_var.set("")
        self.close_day_combo.configure(values=values)

    def toggle_language(self) -> None:
        self.lang = LANG_ZH if self.lang == LANG_EN else LANG_EN
        self._apply_language()

    def _set_result_count(self) -> None:
        self.result_count_var.set(self._t("count_matches", count=len(self.results)))

    def _apply_language(self) -> None:
        self.title(self._t("window_title"))
        self._sync_choice_displays()
        for key, widget in self.label_widgets.items():
            widget.configure(text=self._t(key))
        for key, widget in self.button_widgets.items():
            widget.configure(text=self._t(key))
        for key, widget in self.trait_widgets.items():
            widget.configure(text=localized_trait(self.lang, key))
        if hasattr(self, "source_combo"):
            self.source_combo.configure(values=self._choice_values("source"))
        if hasattr(self, "match_mode_combo"):
            self.match_mode_combo.configure(values=self._choice_values("match_mode"))
        if hasattr(self, "close_year_combo"):
            self.close_year_combo.configure(values=[str(CURRENT_YEAR)])
        if hasattr(self, "close_month_combo"):
            self.close_month_combo.configure(values=MONTH_OPTIONS)
            self._refresh_close_day_options()
        if hasattr(self, "tree"):
            for column in DISPLAY_COLUMNS:
                self.tree.heading(column, text=localized_column(self.lang, column))
        if hasattr(self, "news_tree"):
            for column in NEWS_COLUMNS:
                self.news_tree.heading(column, text=localized_news_column(self.lang, column))
        if hasattr(self, "news_filter_combo"):
            self.news_filter_display_var.set(localized_news_category(self.lang, self.news_filter_key))
            self.news_filter_combo.configure(values=self._news_category_values())
        if hasattr(self, "right_notebook"):
            self.right_notebook.tab(self.results_tab, text=self._t("tab_results"))
            self.right_notebook.tab(self.news_tab, text=self._t("tab_news"))
        if hasattr(self, "result_count_var"):
            self._set_result_count()
        if hasattr(self, "news_count_var"):
            self.news_count_var.set(self._t("count_news", count=len(self.news_results)))
        if hasattr(self, "status_var") and not (self.worker and self.worker.is_alive()):
            self.status_var.set(self._t("status_ready"))
        if hasattr(self, "news_status_var") and not (self.news_worker and self.news_worker.is_alive()):
            self.news_status_var.set(self._news_done_status() if self.news_results else self._t("news_status_ready"))
        if self.results and hasattr(self, "tree"):
            self.refresh_table()
        if self.news_results and hasattr(self, "news_tree"):
            self.refresh_news_table()
            self.start_summary_translation()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        font_families = set(self.tk.call("font", "families"))
        font_family = "Segoe UI Variable" if "Segoe UI Variable" in font_families else "Segoe UI"
        display_family = "Segoe UI Variable Display" if "Segoe UI Variable Display" in font_families else font_family
        base_font = (font_family, 10)
        style.configure(".", background=APP_BG, foreground=TEXT, fieldbackground=FIELD_BG, font=base_font)
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Sidebar.TFrame", background=PANEL_BG)
        style.configure("Content.TFrame", background=APP_BG)
        style.configure("Divider.TFrame", background=BORDER)
        style.configure("Section.TFrame", background=CARD_BG, borderwidth=1, relief="solid", bordercolor=BORDER)
        style.configure("Table.TFrame", background=APP_BG)
        style.configure("Toolbar.TFrame", background=PANEL_BG)
        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#ffffff", foreground=MUTED, padding=(16, 8), borderwidth=1, font=(font_family, 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", CARD_BG), ("active", "#f2f2f7")], foreground=[("selected", TEXT), ("active", TEXT)])
        style.configure("TLabel", background=APP_BG, foreground=TEXT)
        style.configure("Title.TLabel", background=PANEL_BG, foreground=TEXT, font=(display_family, 17, "bold"))
        style.configure("Subtitle.TLabel", background=PANEL_BG, foreground=MUTED, font=(font_family, 9))
        style.configure("PageTitle.TLabel", background=APP_BG, foreground=TEXT, font=(display_family, 22, "bold"))
        style.configure("Muted.TLabel", background=APP_BG, foreground=MUTED, font=base_font)
        style.configure("Badge.TLabel", background=CARD_BG, foreground=MUTED, padding=(14, 6), font=(font_family, 10, "bold"), borderwidth=1, relief="solid", bordercolor=BORDER)
        style.configure("SectionTitle.TLabel", background=CARD_BG, foreground=TEXT, font=(font_family, 11, "bold"))
        style.configure("SectionSubtle.TLabel", background=CARD_BG, foreground=SUBTLE, font=(font_family, 9))
        style.configure("FieldLabel.TLabel", background=CARD_BG, foreground=MUTED, font=(font_family, 9))
        style.configure("Section.TCheckbutton", background=CARD_BG, foreground=TEXT, font=base_font)
        style.map("Section.TCheckbutton", foreground=[("active", TEXT)], background=[("active", CARD_BG)])
        style.configure("TButton", background="#ffffff", foreground=TEXT, padding=(14, 10), borderwidth=1, relief="solid", bordercolor=BORDER, font=(font_family, 10, "bold"))
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", padding=(14, 10), borderwidth=0, font=(font_family, 10, "bold"))
        style.configure("Quiet.TButton", background="#ffffff", foreground=MUTED, padding=(14, 10), borderwidth=1, relief="solid", bordercolor=BORDER, font=(font_family, 10, "bold"))
        style.map(
            "Accent.TButton",
            background=[("active", "#147ce5"), ("disabled", "#b7d7f5")],
            foreground=[("disabled", "#f7fbff")],
        )
        style.map("TButton", background=[("active", "#f2f2f7"), ("disabled", "#f5f5f7")], foreground=[("disabled", "#a1a1aa")])
        style.configure(
            "Modern.TEntry",
            fieldbackground=FIELD_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(10, 8),
            insertcolor=TEXT,
        )
        style.configure(
            "Modern.TCombobox",
            fieldbackground=FIELD_BG,
            background=FIELD_BG,
            foreground=TEXT,
            arrowcolor=MUTED,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(10, 8),
        )
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor="#e5e5ea",
            background=ACCENT,
            bordercolor=APP_BG,
            lightcolor=ACCENT,
            darkcolor=ACCENT_DARK,
        )
        style.configure("Vertical.TScrollbar", background=PANEL_BG, troughcolor="#f2f2f7", bordercolor=PANEL_BG, arrowcolor=MUTED)
        style.configure("Horizontal.TScrollbar", background=APP_BG, troughcolor="#f2f2f7", bordercolor=APP_BG, arrowcolor=MUTED)
        style.configure("Treeview", background="#ffffff", foreground=TEXT, fieldbackground="#ffffff", rowheight=32, borderwidth=0)
        style.configure("Treeview.Heading", background="#f5f5f7", foreground=MUTED, font=(font_family, 9, "bold"), padding=(10, 9))
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", TEXT)])

    def _build_layout(self) -> None:
        self.title(self._t("window_title"))
        self.geometry("1480x900")
        self.minsize(1200, 740)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        shell = ttk.Frame(self, style="App.TFrame", padding=0)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(2, weight=1)

        left = ttk.Frame(shell, style="Sidebar.TFrame", padding=(24, 24, 16, 24))
        left.grid(row=0, column=0, sticky="nsw")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        title = ttk.Label(left, text=self._t("app_title"), style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        self.label_widgets["app_title"] = title
        subtitle = ttk.Label(left, text=self._t("app_subtitle"), style="Subtitle.TLabel")
        subtitle.grid(row=0, column=0, sticky="sw", pady=(28, 0))
        self.label_widgets["app_subtitle"] = subtitle

        sidebar = self._build_scroll_area(left)
        self._build_sidebar_controls(sidebar)
        self._build_action_bar(left)
        ttk.Frame(shell, style="Divider.TFrame", width=1).grid(row=0, column=1, sticky="ns")
        self._build_results_area(shell)

    def _build_scroll_area(self, parent: ttk.Frame) -> ttk.Frame:
        host = ttk.Frame(parent, style="Sidebar.TFrame")
        host.grid(row=1, column=0, sticky="nsew", pady=(22, 16))
        host.rowconfigure(0, weight=1)
        host.columnconfigure(0, weight=1)

        canvas = tk.Canvas(host, bg=PANEL_BG, highlightthickness=0, bd=0, width=374)
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        body = ttk.Frame(canvas, style="Sidebar.TFrame", padding=(0, 0, 8, 0))
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        def update_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_body_width(event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        body.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", fit_body_width)
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        return body

    def _section(self, parent: ttk.Frame, title_key: str) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Section.TFrame", padding=(16, 14))
        frame.pack(fill="x", pady=(0, 14))
        frame.columnconfigure(1, weight=1)
        label = ttk.Label(frame, text=self._t(title_key), style="SectionTitle.TLabel")
        label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.label_widgets[title_key] = label
        return frame

    def _field(self, parent: ttk.Frame, row: int, label_key: str, variable: tk.Variable, values: list[str] | None = None) -> tuple[int, ttk.Widget]:
        label = ttk.Label(parent, text=self._t(label_key), style="FieldLabel.TLabel")
        label.grid(row=row, column=0, sticky="w", pady=5, padx=(0, 12))
        self.label_widgets[label_key] = label
        if values is None:
            widget = ttk.Entry(parent, textvariable=variable, style="Modern.TEntry")
        else:
            widget = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", style="Modern.TCombobox")
        widget.grid(row=row, column=1, sticky="ew", pady=5)
        return row + 1, widget

    def _build_sidebar_controls(self, parent: ttk.Frame) -> None:
        source = self._section(parent, "section_universe")
        row = 1
        row, self.source_combo = self._field(source, row, "field_source", self.source_display_var, self._choice_values("source"))
        self.source_combo.bind("<<ComboboxSelected>>", self._on_source_selected)
        row, _ = self._field(source, row, "field_period", self.period_var)
        row, self.close_year_combo = self._field(source, row, "field_close_year", self.close_year_var, [str(CURRENT_YEAR)])
        row, self.close_month_combo = self._field(source, row, "field_close_month", self.close_month_var, MONTH_OPTIONS)
        self.close_month_combo.bind("<<ComboboxSelected>>", self._on_close_month_selected)
        row, self.close_day_combo = self._field(source, row, "field_close_day", self.close_day_var, day_options_for(CURRENT_YEAR, self.close_month_var.get()))
        row, _ = self._field(source, row, "field_max_symbols", self.max_symbols_var)
        _, self.match_mode_combo = self._field(source, row, "field_match_mode", self.match_mode_display_var, self._choice_values("match_mode"))
        self.match_mode_combo.bind("<<ComboboxSelected>>", self._on_match_mode_selected)

        manual = self._section(parent, "section_manual")
        self.symbol_text = tk.Text(
            manual,
            width=34,
            height=5,
            bg=FIELD_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            padx=10,
            pady=8,
            font=("Cascadia Mono", 10),
        )
        self.symbol_text.insert("1.0", DEFAULT_SYMBOLS)
        self.symbol_text.grid(row=1, column=0, columnspan=2, sticky="ew")

        thresholds = self._section(parent, "section_thresholds")
        row = 1
        for label_key, variable in [
            ("field_mover_ratio", self.min_mover_ratio_var),
            ("field_mover_turnover", self.min_mover_turnover_var),
            ("field_min_move_pct", self.min_move_pct_var),
            ("field_mover_market_cap", self.min_mover_market_cap_var),
            ("field_min_price", self.min_price_var),
            ("field_pattern_market_cap", self.min_pattern_market_cap_var),
            ("field_daily_turnover", self.min_daily_turnover_var),
            ("field_ema_bullish_days", self.ema_bullish_days_var),
            ("field_range_days", self.range_days_var),
            ("field_range_width_pct", self.range_width_pct_var),
            ("field_box_days", self.box_days_var),
            ("field_box_width_pct", self.box_width_pct_var),
            ("field_breakout_turnover", self.min_breakout_turnover_var),
            ("field_breakout_multiple", self.breakout_turnover_multiple_var),
        ]:
            row, _ = self._field(thresholds, row, label_key, variable)
        self.allow_missing_check = ttk.Checkbutton(
            thresholds,
            text=self._t("allow_missing_market_cap"),
            variable=self.allow_missing_market_cap_var,
            style="Section.TCheckbutton",
        )
        self.allow_missing_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.button_widgets["allow_missing_market_cap"] = self.allow_missing_check

        traits = self._section(parent, "section_traits")
        for index, key in enumerate(TRAIT_LABELS, start=1):
            check = ttk.Checkbutton(traits, text=localized_trait(self.lang, key), variable=self.trait_vars[key], style="Section.TCheckbutton")
            check.grid(
                row=index,
                column=0,
                columnspan=2,
                sticky="w",
                pady=4,
            )
            self.trait_widgets[key] = check

    def _build_action_bar(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, style="Toolbar.TFrame")
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        self.scan_button = ttk.Button(actions, text=self._t("button_scan"), command=self.start_scan, style="Accent.TButton")
        self.scan_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.button_widgets["button_scan"] = self.scan_button
        self.stop_button = ttk.Button(actions, text=self._t("button_stop"), command=self.stop_scan, state="disabled", style="Quiet.TButton")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.button_widgets["button_stop"] = self.stop_button
        export_button = ttk.Button(actions, text=self._t("button_export"), command=self.export_csv)
        export_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.button_widgets["button_export"] = export_button
        language_button = ttk.Button(actions, text=self._t("button_language"), command=self.toggle_language, style="Quiet.TButton")
        language_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.button_widgets["button_language"] = language_button

    def _build_results_area(self, parent: ttk.Frame) -> None:
        right = ttk.Frame(parent, style="Content.TFrame", padding=(30, 28, 30, 30))
        right.grid(row=0, column=2, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        header = ttk.Frame(right, style="Content.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        results_title = ttk.Label(header, text=self._t("results_title"), style="PageTitle.TLabel")
        results_title.grid(row=0, column=0, sticky="w")
        self.label_widgets["results_title"] = results_title
        self.result_count_var = tk.StringVar(value=self._t("count_matches", count=0))
        ttk.Label(header, textvariable=self.result_count_var, style="Badge.TLabel").grid(row=0, column=1, sticky="e")

        status = ttk.Frame(right, style="Section.TFrame", padding=(16, 14))
        status.grid(row=1, column=0, sticky="ew", pady=(18, 18))
        status.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value=self._t("status_ready"))
        ttk.Label(status, textvariable=self.status_var, style="SectionSubtle.TLabel").grid(row=0, column=0, sticky="ew")
        self.progress = ttk.Progressbar(status, mode="indeterminate", style="Modern.Horizontal.TProgressbar")
        self.progress.grid(row=0, column=1, sticky="ew", padx=(14, 0))

        self.right_notebook = ttk.Notebook(right)
        self.right_notebook.grid(row=2, column=0, sticky="nsew")
        self.results_tab = ttk.Frame(self.right_notebook, style="Content.TFrame", padding=(0, 8, 0, 0))
        self.news_tab = ttk.Frame(self.right_notebook, style="Content.TFrame", padding=(0, 8, 0, 0))
        self.right_notebook.add(self.results_tab, text=self._t("tab_results"))
        self.right_notebook.add(self.news_tab, text=self._t("tab_news"))
        self.results_tab.rowconfigure(0, weight=1)
        self.results_tab.columnconfigure(0, weight=1)
        self.news_tab.rowconfigure(2, weight=1)
        self.news_tab.columnconfigure(0, weight=1)

        table_frame = ttk.Frame(self.results_tab, style="Table.TFrame")
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=DISPLAY_COLUMNS, show="headings")
        widths = {
            "symbol": 92,
            "last_date": 112,
            "match_count": 82,
            "matched_traits": 270,
            "close": 95,
            "move_pct": 95,
            "gap_pct": 95,
            "mover_ratio": 110,
            "turnover": 140,
            "market_cap": 140,
            "box_width_pct": 125,
            "breakout_side": 110,
            "ema5": 100,
            "ema10": 100,
            "ema20": 100,
            "ema_bullish_days": 112,
            "range_width_pct": 125,
            "range_days": 100,
        }
        for column in DISPLAY_COLUMNS:
            self.tree.heading(column, text=localized_column(self.lang, column), anchor="center")
            self.tree.column(column, width=widths.get(column, 120), anchor="center", stretch=False)
        self.tree.tag_configure("gain", foreground=GAIN)
        self.tree.tag_configure("loss", foreground=LOSS)
        self.tree.tag_configure("neutral", foreground=MUTED)
        self.tree.tag_configure("odd", background="#fbfbfd")
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self._build_news_tab(self.news_tab)

    def _build_news_tab(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Content.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        news_title = ttk.Label(header, text=self._t("news_title"), style="PageTitle.TLabel")
        news_title.grid(row=0, column=0, sticky="w")
        self.label_widgets["news_title"] = news_title
        self.news_count_var = tk.StringVar(value=self._t("count_news", count=0))
        ttk.Label(header, textvariable=self.news_count_var, style="Badge.TLabel").grid(row=0, column=1, sticky="e")

        controls = ttk.Frame(parent, style="Section.TFrame", padding=(16, 14))
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for column in range(4):
            controls.columnconfigure(column, weight=1, uniform="news_controls")

        news_fields = [
            ("field_news_max_symbols", self.news_max_symbols_var),
            ("field_news_items", self.news_items_per_symbol_var),
            ("field_news_days", self.news_recent_days_var),
        ]
        for column, (label_key, variable) in enumerate(news_fields):
            label = ttk.Label(controls, text=self._t(label_key), style="FieldLabel.TLabel")
            label.grid(row=0, column=column, sticky="w", padx=(0, 10))
            self.label_widgets[label_key] = label
            if label_key == "field_news_days":
                self.news_days_combo = ttk.Combobox(
                    controls,
                    textvariable=variable,
                    values=NEWS_DAY_RANGE_OPTIONS,
                    state="readonly",
                    justify="center",
                    style="Modern.TCombobox",
                )
                field_widget = self.news_days_combo
            else:
                field_widget = ttk.Entry(controls, textvariable=variable, style="Modern.TEntry", justify="center")
            field_widget.grid(row=1, column=column, sticky="ew", padx=(0, 10), pady=(5, 0))

        category_label = ttk.Label(controls, text=self._t("field_news_category"), style="FieldLabel.TLabel")
        category_label.grid(row=0, column=3, sticky="w")
        self.label_widgets["field_news_category"] = category_label
        self.news_filter_combo = ttk.Combobox(
            controls,
            textvariable=self.news_filter_display_var,
            values=self._news_category_values(),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.news_filter_combo.grid(row=1, column=3, sticky="ew", pady=(5, 0))
        self.news_filter_combo.bind("<<ComboboxSelected>>", self._on_news_category_selected)

        self.load_news_button = ttk.Button(
            controls,
            text=self._t("button_load_news"),
            command=self.start_news_load,
            style="Accent.TButton",
        )
        self.load_news_button.grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(14, 0))
        self.button_widgets["button_load_news"] = self.load_news_button
        self.stop_news_button = ttk.Button(
            controls,
            text=self._t("button_stop_news"),
            command=self.stop_news_load,
            state="disabled",
            style="Quiet.TButton",
        )
        self.stop_news_button.grid(row=2, column=1, sticky="ew", padx=6, pady=(14, 0))
        self.button_widgets["button_stop_news"] = self.stop_news_button
        export_news_button = ttk.Button(controls, text=self._t("button_export_news"), command=self.export_news_csv)
        export_news_button.grid(row=2, column=2, sticky="ew", padx=6, pady=(14, 0))
        self.button_widgets["button_export_news"] = export_news_button
        open_news_button = ttk.Button(controls, text=self._t("button_open_news"), command=self.open_selected_news_link)
        open_news_button.grid(row=2, column=3, sticky="ew", padx=(6, 0), pady=(14, 0))
        self.button_widgets["button_open_news"] = open_news_button

        self.news_status_var = tk.StringVar(value=self._t("news_status_ready"))
        ttk.Label(controls, textvariable=self.news_status_var, style="SectionSubtle.TLabel").grid(
            row=3,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(12, 0),
        )

        table_frame = ttk.Frame(parent, style="Table.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.news_tree = ttk.Treeview(table_frame, columns=NEWS_COLUMNS, show="headings")
        widths = {
            "symbol": 90,
            "time": 150,
            "category": 150,
            "source": 150,
            "headline": 430,
            "summary": 560,
        }
        for column in NEWS_COLUMNS:
            self.news_tree.heading(column, text=localized_news_column(self.lang, column), anchor="center")
            self.news_tree.column(column, width=widths.get(column, 130), anchor="center", stretch=False)
        self.news_tree.tag_configure("odd", background="#fbfbfd")
        self.news_tree.grid(row=0, column=0, sticky="nsew")
        self.news_tree.bind("<Double-1>", lambda _event: self.open_selected_news_link())
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.news_tree.yview, style="Vertical.TScrollbar")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.news_tree.xview, style="Horizontal.TScrollbar")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.news_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def read_config(self) -> ScannerConfig:
        symbols = parse_symbols(self.symbol_text.get("1.0", "end"))
        max_symbols = max(0, int(self.max_symbols_var.get()))
        target_date = None
        raw_month = self.close_month_var.get().strip()
        raw_day = self.close_day_var.get().strip()
        if bool(raw_month) != bool(raw_day):
            raise ValueError(self._t("dlg_invalid_date_body"))
        if not raw_month and not raw_day:
            raw_month = DEFAULT_MONTH
            raw_day = DEFAULT_DAY
        try:
            target_date = pd.Timestamp(f"{CURRENT_YEAR}-{raw_month}-{raw_day}")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(self._t("dlg_invalid_date_body")) from exc
        return ScannerConfig(
            source_mode=self.source_mode_var.get(),
            symbols=symbols[:max_symbols] if max_symbols > 0 else symbols,
            period=self.period_var.get().strip() or "2y",
            target_date=target_date,
            selected_traits={key for key, var in self.trait_vars.items() if var.get()},
            match_mode=self.match_mode_var.get(),
            max_symbols=max_symbols,
            min_mover_ratio=to_float(self.min_mover_ratio_var.get()),
            min_mover_turnover=to_float(self.min_mover_turnover_var.get()),
            min_move_pct=to_float(self.min_move_pct_var.get()),
            min_mover_market_cap=to_float(self.min_mover_market_cap_var.get()),
            min_price=to_float(self.min_price_var.get()),
            min_pattern_market_cap=to_float(self.min_pattern_market_cap_var.get()),
            allow_missing_market_cap=self.allow_missing_market_cap_var.get(),
            min_daily_turnover=to_float(self.min_daily_turnover_var.get()),
            ema_bullish_days=max(1, int(self.ema_bullish_days_var.get())),
            range_days=max(1, int(self.range_days_var.get())),
            range_width_pct=to_float(self.range_width_pct_var.get()),
            box_days=max(5, int(self.box_days_var.get())),
            box_width_pct=to_float(self.box_width_pct_var.get()),
            min_breakout_turnover=to_float(self.min_breakout_turnover_var.get()),
            breakout_turnover_multiple=to_float(self.breakout_turnover_multiple_var.get()),
        )

    def start_scan(self) -> None:
        if yf is None or pd is None:
            messagebox.showerror(self._t("dlg_missing_dep_title"), self._t("dlg_missing_dep_body"))
            return
        try:
            config = self.read_config()
        except ValueError as exc:
            messagebox.showerror(self._t("dlg_invalid_input_title"), str(exc))
            return
        if config.source_mode == SOURCE_MANUAL and not config.symbols:
            messagebox.showinfo(self._t("dlg_no_symbols_title"), self._t("dlg_no_symbols_body"))
            return
        self.results.clear()
        self.clear_table()
        self._set_result_count()
        self.stop_event.clear()
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set(self._t("status_preparing"))
        self.progress.start(12)
        self.worker = threading.Thread(target=self.scan_worker, args=(config,), daemon=True)
        self.worker.start()

    def stop_scan(self) -> None:
        self.stop_event.set()
        self.status_var.set(self._t("status_stopping"))

    def scan_worker(self, config: ScannerConfig) -> None:
        try:
            symbols = list(config.symbols)
            if config.source_mode == SOURCE_UNIVERSE:
                self.messages.put(("status", self._t("status_loading_universe")))
                symbols = load_symbol_directory()
                if config.max_symbols > 0:
                    symbols = symbols[: config.max_symbols]
            if not symbols:
                self.messages.put(("error", self._t("err_no_symbols_to_scan")))
                return
            rows: list[dict] = []
            total = len(symbols)
            checked = 0
            for batch in chunks(symbols, 80):
                if self.stop_event.is_set():
                    break
                self.messages.put(
                    (
                        "status",
                        self._t("status_downloading", start=checked + 1, end=min(checked + len(batch), total), total=total),
                    )
                )
                raw = yf.download(
                    tickers=" ".join(batch),
                    period=config.period,
                    interval="1d",
                    group_by="ticker",
                    auto_adjust=True,
                    threads=True,
                    progress=False,
                    timeout=30,
                )
                for symbol in batch:
                    if self.stop_event.is_set():
                        break
                    checked += 1
                    self.messages.put(("status", self._t("status_checking", symbol=symbol, checked=checked, total=total)))
                    frame = get_symbol_frame(raw, symbol, len(batch))
                    daily = normalize_history(frame)
                    daily = history_as_of_date(daily, config.target_date)
                    if daily is None or len(daily) < 21:
                        continue
                    row = add_traits(base_row(symbol, daily, 0.0), daily, config)
                    if row.get("_trait_pass"):
                        rows.append(row)
                    time.sleep(0.03)
                self.messages.put(("rows", sorted(rows, key=lambda item: (to_float(item.get("match_count")), to_float(item.get("turnover"))), reverse=True)))
            rows.sort(key=lambda item: (to_float(item.get("match_count")), to_float(item.get("turnover"))), reverse=True)
            self.messages.put(("rows", rows))
            self.messages.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self.messages.put(("error", str(exc)))

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "rows":
                    self.results = list(payload)
                    self.refresh_table()
                elif kind == "error":
                    self.status_var.set(self._t("status_error"))
                    messagebox.showerror(self._t("dlg_scan_failed_title"), str(payload))
                    self.scan_finished()
                elif kind == "done":
                    self.status_var.set(self._t("status_done", count=len(self.results)))
                    self.scan_finished()
                elif kind == "news_status":
                    self.news_status_var.set(str(payload))
                elif kind == "news_rows":
                    self.news_results = list(payload)
                    self.refresh_news_table()
                elif kind == "news_done":
                    self.news_status_var.set(self._news_done_status())
                    self.news_finished()
                    self.start_summary_translation()
                elif kind == "summary_translation":
                    text, translated, failed, done, total = payload
                    if translated:
                        self.summary_translations[str(text)] = str(translated)
                    if failed:
                        self.summary_translation_failures.add(str(text))
                    if self.lang == LANG_ZH:
                        self.news_status_var.set(self._t("news_status_translating", done=done, total=total))
                        self.refresh_news_table()
                elif kind == "summary_translation_done":
                    self.summary_translation_worker = None
                    if self.lang == LANG_ZH:
                        self.refresh_news_table()
                        self.news_status_var.set(self._news_done_status())
                    self.start_summary_translation()
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def scan_finished(self) -> None:
        self.progress.stop()
        self.scan_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.stop_event.clear()

    def news_symbols(self, max_symbols: int) -> list[str]:
        result_symbols = [str(row.get("symbol", "")).strip().upper() for row in self.results]
        manual_symbols = parse_symbols(self.symbol_text.get("1.0", "end"))
        symbols = [*result_symbols, *manual_symbols]
        symbols = [symbol for symbol in dict.fromkeys(symbols) if symbol]
        return symbols[:max_symbols]

    def _news_done_status(self) -> str:
        return self._t(
            "news_status_done",
            count=len(self.news_results),
            start_date=self.news_range_start.isoformat(),
            end_date=self.news_range_end.isoformat(),
        )

    def start_news_load(self) -> None:
        if yf is None:
            messagebox.showerror(self._t("dlg_missing_dep_title"), self._t("dlg_missing_dep_body"))
            return
        try:
            max_symbols = max(1, int(self.news_max_symbols_var.get()))
            items_per_search = max(1, int(self.news_items_per_symbol_var.get()))
            recent_days = max(1, int(self.news_recent_days_var.get()))
        except ValueError:
            messagebox.showerror(self._t("dlg_invalid_input_title"), self._t("dlg_invalid_number_body"))
            return
        self.news_range_start, self.news_range_end = news_date_range(recent_days)
        symbols = self.news_symbols(max_symbols)
        self.summary_translation_stop_event.set()
        self.news_results.clear()
        self.clear_news_table()
        self.news_count_var.set(self._t("count_news", count=0))
        self.news_stop_event.clear()
        self.load_news_button.configure(state="disabled")
        self.stop_news_button.configure(state="normal")
        self.news_status_var.set(self._t("news_status_loading", symbol="News", checked=0, total=1))
        self.news_worker = threading.Thread(
            target=self.load_news_worker,
            args=(symbols, items_per_search, recent_days),
            daemon=True,
        )
        self.news_worker.start()

    def stop_news_load(self) -> None:
        self.news_stop_event.set()
        self.news_status_var.set(self._t("news_status_stopping"))

    def load_news_worker(
        self,
        symbols: list[str],
        items_per_search: int,
        recent_days: int,
    ) -> None:
        rows: list[dict] = []
        self.messages.put(("news_status", self._t("news_status_loading_tech_universe")))
        technology_aliases = load_us_listed_technology_aliases()
        tasks: list[tuple[str, str, str, str]] = []
        tasks.extend(
            (
                "google",
                NEWS_TECH_COMPANY,
                f"{query} when:{recent_days}d",
                localized_news_category(self.lang, NEWS_TECH_COMPANY),
            )
            for query in GOOGLE_TECH_UPDATE_SEARCHES
        )
        for category in [NEWS_MARKET_VIEWS, NEWS_BANK_RESEARCH]:
            queries = NEWS_TOPIC_SEARCHES.get(category, [])
            tasks.extend(("topic", category, query, localized_news_category(self.lang, category)) for query in queries)
            tasks.extend(
                (
                    "google",
                    category,
                    f"{query} when:{recent_days}d",
                    localized_news_category(self.lang, category),
                )
                for query in GOOGLE_FOCUSED_TOPIC_SEARCHES.get(category, [])
            )
        tasks.extend(("symbol", NEWS_TECH_COMPANY, symbol, symbol) for symbol in symbols)
        for category, queries in NEWS_TOPIC_SEARCHES.items():
            if category in {NEWS_MARKET_VIEWS, NEWS_BANK_RESEARCH}:
                continue
            tasks.extend(("topic", category, query, localized_news_category(self.lang, category)) for query in queries)
        total = len(tasks)
        for index, (task_type, category, query, label) in enumerate(tasks, start=1):
            if self.news_stop_event.is_set():
                break
            self.messages.put(("news_status", self._t("news_status_loading", symbol=label, checked=index, total=total)))
            if task_type == "symbol":
                rows.extend(fetch_technology_company_news(query, items_per_search, recent_days))
            elif task_type == "google":
                rows.extend(
                    fetch_google_news_rss(
                        query,
                        category,
                        max(items_per_search * 10, 100),
                        recent_days,
                        company_aliases=technology_aliases if category == NEWS_TECH_COMPANY else None,
                    )
                )
            else:
                rows.extend(fetch_topic_news(category, query, items_per_search, recent_days))
            rows = deduplicate_news(rows)
            self.messages.put(("news_rows", list(rows)))
            time.sleep(0.05)
        self.messages.put(("news_done", None))

    def news_finished(self) -> None:
        self.load_news_button.configure(state="normal")
        self.stop_news_button.configure(state="disabled")
        self.news_stop_event.clear()

    def start_summary_translation(self) -> None:
        if self.lang != LANG_ZH or not self.news_results:
            return
        if self.news_worker and self.news_worker.is_alive():
            return
        if self.summary_translation_worker and self.summary_translation_worker.is_alive():
            return
        texts: list[str] = []
        for row in self.filtered_news_results():
            for field in ("headline", "summary"):
                text = str(row.get(field, "")).strip()
                if not text or text in self.summary_translations or text in self.summary_translation_failures:
                    continue
                if re.search(r"[\u4e00-\u9fff]", text):
                    self.summary_translations[text] = text
                    continue
                if text not in texts:
                    texts.append(text)
        if not texts:
            self.refresh_news_table()
            return
        self.summary_translation_stop_event.clear()
        self.news_status_var.set(self._t("news_status_translating", done=0, total=len(texts)))
        self.summary_translation_worker = threading.Thread(
            target=self.translate_summary_worker,
            args=(texts,),
            daemon=True,
        )
        self.summary_translation_worker.start()

    def translate_summary_worker(self, texts: list[str]) -> None:
        total = len(texts)
        for index, text in enumerate(texts, start=1):
            if self.summary_translation_stop_event.is_set():
                break
            translated = translate_summary_to_chinese(text)
            self.messages.put(("summary_translation", (text, translated, not translated, index, total)))
            time.sleep(0.05)
        self.messages.put(("summary_translation_done", None))

    def localized_news_text(self, value, pending_placeholder: bool = True) -> str:
        original = str(value or "")
        if self.lang != LANG_ZH or not original:
            return original
        translated = self.summary_translations.get(original)
        if translated:
            return translated
        if original in self.summary_translation_failures:
            return self._t("summary_translation_failed", text=original)
        return self._t("summary_translating") if pending_placeholder else original

    def refresh_news_table(self) -> None:
        self.clear_news_table()
        visible_rows = self.filtered_news_results()
        self.news_count_var.set(self._t("count_news", count=len(visible_rows)))
        for index, row in enumerate(visible_rows):
            values = []
            for column in NEWS_COLUMNS:
                value = row.get(column, "")
                if column == "category":
                    values.append(localized_news_category(self.lang, str(value)))
                elif column in {"headline", "summary"}:
                    values.append(self.localized_news_text(value))
                else:
                    values.append(str(value))
            tags = ("odd",) if index % 2 else ()
            item_id = self.news_tree.insert("", "end", values=values, tags=tags)
            self.news_item_links[item_id] = str(row.get("link", "") or "")

    def filtered_news_results(self) -> list[dict]:
        if self.news_filter_key == NEWS_ALL:
            return list(self.news_results)
        return [row for row in self.news_results if row.get("category") == self.news_filter_key]

    def clear_news_table(self) -> None:
        for item in self.news_tree.get_children():
            self.news_tree.delete(item)
        self.news_item_links.clear()

    def selected_news_link(self) -> str:
        selection = self.news_tree.selection()
        if not selection:
            return ""
        return self.news_item_links.get(selection[0], "")

    def open_selected_news_link(self) -> None:
        link = self.selected_news_link()
        if not link:
            messagebox.showinfo(self._t("dlg_no_news_link_title"), self._t("dlg_no_news_link_body"))
            return
        webbrowser.open(link)

    def export_news_csv(self) -> None:
        visible_rows = self.filtered_news_results()
        if not visible_rows:
            messagebox.showinfo(self._t("dlg_no_news_title"), self._t("dlg_no_news_body"))
            return
        path = filedialog.asksaveasfilename(
            title=self._t("news_export_title"),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="yfinance_news_results.csv",
        )
        if not path:
            return
        with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=NEWS_COLUMNS)
            writer.writeheader()
            for row in visible_rows:
                output = {column: row.get(column, "") for column in NEWS_COLUMNS}
                output["category"] = localized_news_category(self.lang, str(output.get("category", "")))
                output["headline"] = self.localized_news_text(row.get("headline", ""), pending_placeholder=False)
                output["summary"] = self.localized_news_text(row.get("summary", ""), pending_placeholder=False)
                writer.writerow(output)
        messagebox.showinfo(self._t("dlg_exported_title"), self._t("dlg_exported_body", count=len(visible_rows)))

    def refresh_table(self) -> None:
        self.clear_table()
        self._set_result_count()
        for index, row in enumerate(self.results):
            values = []
            for column in DISPLAY_COLUMNS:
                value = row.get(column, "")
                if column == "matched_traits":
                    trait_keys = row.get("_matched_trait_keys") or []
                    values.append(", ".join(localized_trait(self.lang, key) for key in trait_keys))
                elif column == "breakout_side":
                    values.append(localized_breakout_side(self.lang, str(value)))
                elif column in {"symbol", "last_date"}:
                    values.append(str(value))
                else:
                    values.append(clean_number(value))
            tag = "gain" if to_float(row.get("move_pct")) > 0 else "loss" if to_float(row.get("move_pct")) < 0 else "neutral"
            tags = (tag, "odd") if index % 2 else (tag,)
            self.tree.insert("", "end", values=values, tags=tags)

    def clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_csv(self) -> None:
        if not self.results:
            messagebox.showinfo(self._t("dlg_no_results_title"), self._t("dlg_no_results_body"))
            return
        path = filedialog.asksaveasfilename(
            title=self._t("export_title"),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="yfinance_prototype_results.csv",
        )
        if not path:
            return
        with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=DISPLAY_COLUMNS)
            writer.writeheader()
            for row in self.results:
                output = {column: row.get(column, "") for column in DISPLAY_COLUMNS}
                output["matched_traits"] = ", ".join(localized_trait(self.lang, key) for key in row.get("_matched_trait_keys", []))
                output["breakout_side"] = localized_breakout_side(self.lang, str(output.get("breakout_side", "")))
                writer.writerow(output)
        messagebox.showinfo(self._t("dlg_exported_title"), self._t("dlg_exported_body", count=len(self.results)))


if __name__ == "__main__":
    app = YFinancePrototypeScanner()
    app.mainloop()
