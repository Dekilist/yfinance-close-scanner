from __future__ import annotations

import csv
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import pandas as pd
    from futu import AuType, KLType, Market, OpenQuoteContext, Plate, RET_OK, SecurityType
except ImportError:
    AuType = KLType = Market = OpenQuoteContext = Plate = RET_OK = SecurityType = None
    pd = None


TRAIT_VOLUME_SURGE = "volume_surge"
TRAIT_BOX_BREAKOUT = "box_breakout"
TRAIT_EMA_CONVERGED = "ema_converged"
TRAIT_NEAR_EMA20 = "near_ema20"
TRAIT_NEAR_EMA50 = "near_ema50"
TRAIT_NEAR_EMA200 = "near_ema200"

TRAIT_LABELS = {
    TRAIT_VOLUME_SURGE: "+/-10% close mover",
    TRAIT_BOX_BREAKOUT: "20D turnover box breakout",
    TRAIT_EMA_CONVERGED: "EMA5/10/20 tight flat/up 5D+",
    TRAIT_NEAR_EMA20: "Near rising EMA20",
    TRAIT_NEAR_EMA50: "Near rising EMA50",
    TRAIT_NEAR_EMA200: "Near rising EMA200",
}

TRAIT_LABELS_BY_LANG = {
    "en": TRAIT_LABELS,
    "zh": {
        TRAIT_VOLUME_SURGE: "收盘涨跌10%+",
        TRAIT_BOX_BREAKOUT: "20日箱体放量突破",
        TRAIT_EMA_CONVERGED: "EMA5/10/20粘连走平向上",
        TRAIT_NEAR_EMA20: "股价靠近上升EMA20",
        TRAIT_NEAR_EMA50: "股价靠近上升EMA50",
        TRAIT_NEAR_EMA200: "股价靠近上升EMA200",
    },
}

DISPLAY_COLUMNS = [
    "code",
    "name",
    "update_time",
    "match_count",
    "matched_traits",
    "scan_price",
    "day_change_rate",
    "gap_pct",
    "volume_ratio",
    "volume",
    "turnover",
    "turnover_rate",
    "amplitude",
    "box_high_20",
    "box_low_20",
    "box_width_pct",
    "breakout_side",
    "ema5",
    "ema10",
    "ema20",
    "ema50",
    "ema200",
    "near_ema",
    "total_market_val",
]

SNAPSHOT_COLUMNS = [
    "code",
    "name",
    "update_time",
    "last_price",
    "open_price",
    "high_price",
    "low_price",
    "prev_close_price",
    "change_val",
    "change_rate",
    "volume",
    "turnover",
    "turnover_rate",
    "volume_ratio",
    "amplitude",
    "after_price",
    "after_high_price",
    "after_low_price",
    "after_change_val",
    "after_change_rate",
    "after_amplitude",
    "after_volume",
    "after_turnover",
    "pe_ttm_ratio",
    "total_market_val",
]

UNSUPPORTED_US_EXCHANGES = {"US_PINK", "US_OTC"}

APP_BG = "#0f1115"
PANEL_BG = "#151922"
PANEL_ALT = "#1b2030"
FIELD_BG = "#10141d"
BORDER = "#2a3140"
TEXT = "#e6e8ee"
MUTED = "#9ba3b4"
ACCENT = "#10a37f"
ACCENT_HOVER = "#13b890"
WARNING = "#f59e0b"
GAIN = "#63d297"
LOSS = "#f87171"

FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI Semibold", 16)
FONT_SECTION = ("Segoe UI Semibold", 10)

COLUMN_LABELS = {
    "code": "Symbol",
    "name": "Name",
    "update_time": "Updated",
    "match_count": "Matches",
    "matched_traits": "Matched Traits",
    "scan_price": "Close Price",
    "day_change_rate": "Close %",
    "gap_pct": "Gap %",
    "volume_ratio": "Mover Ratio",
    "volume": "Volume",
    "turnover": "Turnover",
    "turnover_rate": "Turnover %",
    "amplitude": "Amplitude",
    "box_high_20": "20D Box High",
    "box_low_20": "20D Box Low",
    "box_width_pct": "Box Width %",
    "breakout_side": "Breakout",
    "ema5": "EMA5",
    "ema10": "EMA10",
    "ema20": "EMA20",
    "ema50": "EMA50",
    "ema200": "EMA200",
    "near_ema": "Near EMA",
    "total_market_val": "Market Cap",
}

COLUMN_LABELS_BY_LANG = {
    "en": COLUMN_LABELS,
    "zh": {
        "code": "代码",
        "name": "名称",
        "update_time": "更新时间",
        "match_count": "命中数",
        "matched_traits": "命中特征",
        "scan_price": "收盘价",
        "day_change_rate": "收盘涨幅%",
        "gap_pct": "跳空%",
        "volume_ratio": "量比",
        "volume": "成交量",
        "turnover": "成交额",
        "turnover_rate": "换手率%",
        "amplitude": "振幅",
        "box_high_20": "20日箱体高点",
        "box_low_20": "20日箱体低点",
        "box_width_pct": "箱体宽度%",
        "breakout_side": "突破方向",
        "ema5": "EMA5",
        "ema10": "EMA10",
        "ema20": "EMA20",
        "ema50": "EMA50",
        "ema200": "EMA200",
        "near_ema": "靠近均线",
        "total_market_val": "总市值",
    },
}

UI_TEXT = {
    "en": {
        "app_brand": "Futu Scanner",
        "app_subtitle": "Close-session patterns for the U.S. market",
        "tab_scan": "Scan",
        "tab_traits": "Traits",
        "section_connection": "Connection",
        "opend_host": "OpenD Host",
        "opend_port": "OpenD Port",
        "section_universe": "Universe",
        "source": "Source",
        "source_manual": "Manual Symbols",
        "source_universe": "U.S. Stock Universe",
        "source_sector": "Sector Stocks",
        "symbols": "Symbols",
        "sector_type": "Sector Type",
        "sector": "Sector",
        "load_sectors": "Load Sectors",
        "sector_industry": "Industry",
        "sector_concept": "Concept",
        "sector_region": "Region",
        "sector_other": "Other",
        "sector_all": "All",
        "max_symbols": "Max Symbols",
        "batch_size": "Batch Size",
        "section_after_filters": "Close Filters",
        "min_ah_volume": "Min Volume",
        "min_ah_turnover": "Min Turnover",
        "min_abs_ah_pct": "Min Abs Close %",
        "min_ah_price": "Min Close Price",
        "max_ah_price": "Max Close Price",
        "min_ah_amplitude": "Min Amplitude",
        "direction": "Direction",
        "sort_by": "Sort By",
        "only_active_after_hours": "Only active close-session stocks",
        "scan": "Scan",
        "stop": "Stop",
        "export_csv": "Export CSV",
        "section_technical_traits": "Technical Traits",
        "section_matching": "Matching",
        "match_mode": "Match Mode",
        "section_thresholds": "Thresholds",
        "max_tech_checks": "Max Tech Checks",
        "history_candles": "History Candles",
        "min_mover_ratio": "Mover Ratio",
        "min_market_cap": "Min Market Cap",
        "min_liquidity_turnover": "EMA Daily Turnover",
        "liquidity_days": "Liquidity Days",
        "min_mover_turnover": "Min Mover Turnover",
        "min_breakout_turnover": "Min Breakout Turnover",
        "breakout_turnover_multiple": "Breakout Turnover Multiple",
        "min_price": "Min Price",
        "min_day_gain_pct": "Min Abs Move %",
        "box_days": "Box Days",
        "max_box_width_pct": "Max Box Width %",
        "ema_tight_pct": "EMA Tight %",
        "ema_bull_days": "EMA Lookback Days",
        "near_ema_pct": "Near EMA %",
        "dad_preset": "Preset",
        "results_title": "Close Pattern Scanner",
        "results_subtitle": "Read-only FutuOpenD quote analysis with configurable technical traits.",
        "language_button": "中文",
        "status_initial": "Start FutuOpenD, log in, then scan.",
        "status_connecting": "Connecting to FutuOpenD...",
        "status_stopping": "Stopping after the current request...",
        "status_error": "Error.",
        "status_done": "Done. {count} matches.",
        "status_matches_so_far": "{count} matches so far.",
        "status_loading_universe": "Loading U.S. stock universe...",
        "status_loading_sectors": "Loading U.S. sectors...",
        "status_loaded_sectors": "Loaded {count} sectors. Choose one, then scan.",
        "status_loading_sector_stocks": "Loading stocks from {sector}...",
        "status_loaded_sector_stocks": "Loaded {count} stocks from {sector}.",
        "status_scanning_batches": "Scanning {count} symbols in batches of {batch_size}...",
        "status_snapshot_candidates": "Snapshot scan found {count} close-session candidates.",
        "status_technical_checks": "Checking technical traits on {count} snapshot candidates...",
        "status_no_trait_matches": "Done. No stocks matched the selected technical traits.",
        "missing_api_title": "Missing futu-api",
        "missing_api_message": "Install the SDK first:\n\npython -m pip install -r requirements.txt",
        "invalid_input_title": "Invalid input",
        "no_results_title": "No results",
        "no_results_message": "Run a scan first.",
        "export_title": "Export close-session results",
        "exported_title": "Exported",
        "exported_message": "Saved {count} rows.",
        "scan_failed_title": "Scan failed",
        "no_symbols_message": "No symbols to scan. Add symbols or clear the box for U.S. stocks.",
        "no_sector_message": "Choose a sector first. Click Load Sectors, select a sector, then scan.",
        "dir_any": "Any",
        "dir_gainers": "Gainers",
        "dir_losers": "Losers",
        "match_any": "Any Selected",
        "match_all": "All Selected",
    },
    "zh": {
        "app_brand": "富途收盘扫描",
        "app_subtitle": "美股收盘形态与技术特征筛选",
        "tab_scan": "扫描",
        "tab_traits": "特征",
        "section_connection": "连接",
        "opend_host": "OpenD地址",
        "opend_port": "OpenD端口",
        "section_universe": "股票范围",
        "source": "来源",
        "source_manual": "手动代码",
        "source_universe": "美股全市场",
        "source_sector": "板块股票",
        "symbols": "股票代码",
        "sector_type": "板块类型",
        "sector": "板块",
        "load_sectors": "加载板块",
        "sector_industry": "行业",
        "sector_concept": "概念",
        "sector_region": "地区",
        "sector_other": "其他",
        "sector_all": "全部",
        "max_symbols": "最多股票数",
        "batch_size": "每批数量",
        "section_after_filters": "收盘筛选",
        "min_ah_volume": "最低成交量",
        "min_ah_turnover": "最低成交额",
        "min_abs_ah_pct": "最低收盘涨跌幅",
        "min_ah_price": "最低收盘价",
        "max_ah_price": "最高收盘价",
        "min_ah_amplitude": "最低振幅",
        "direction": "方向",
        "sort_by": "排序",
        "only_active_after_hours": "仅显示当日活跃股票",
        "scan": "开始扫描",
        "stop": "停止",
        "export_csv": "导出CSV",
        "section_technical_traits": "技术特征",
        "section_matching": "匹配方式",
        "match_mode": "匹配模式",
        "section_thresholds": "参数阈值",
        "max_tech_checks": "最多技术检查",
        "history_candles": "历史K线数量",
        "min_mover_ratio": "异动量比",
        "min_market_cap": "最低市值",
        "min_liquidity_turnover": "EMA日成交额",
        "liquidity_days": "流动性天数",
        "min_mover_turnover": "最低异动成交额",
        "min_breakout_turnover": "最低突破成交额",
        "breakout_turnover_multiple": "突破成交额倍数",
        "min_price": "最低股价",
        "min_day_gain_pct": "最低涨跌幅%",
        "box_days": "箱体天数",
        "max_box_width_pct": "最大箱体宽度%",
        "ema_tight_pct": "EMA粘合%",
        "ema_bull_days": "EMA检查天数",
        "near_ema_pct": "靠近EMA%",
        "dad_preset": "参数",
        "results_title": "收盘技术形态扫描",
        "results_subtitle": "只读连接FutuOpenD，按收盘行情和技术特征筛选股票。",
        "language_button": "English",
        "status_initial": "请先启动FutuOpenD并登录，然后开始扫描。",
        "status_connecting": "正在连接FutuOpenD...",
        "status_stopping": "正在停止，等待当前请求结束...",
        "status_error": "出错。",
        "status_done": "完成。共 {count} 个结果。",
        "status_matches_so_far": "当前 {count} 个结果。",
        "status_loading_universe": "正在加载美股股票池...",
        "status_loading_sectors": "正在加载美股板块...",
        "status_loaded_sectors": "已加载 {count} 个板块。请选择板块后开始扫描。",
        "status_loading_sector_stocks": "正在加载 {sector} 的股票...",
        "status_loaded_sector_stocks": "已从 {sector} 加载 {count} 只股票。",
        "status_scanning_batches": "正在扫描 {count} 只股票，每批 {batch_size} 只...",
        "status_snapshot_candidates": "快照扫描找到 {count} 个收盘候选。",
        "status_technical_checks": "正在对 {count} 个候选做技术特征检查...",
        "status_no_trait_matches": "完成。没有股票符合所选技术特征。",
        "missing_api_title": "缺少 futu-api",
        "missing_api_message": "请先安装SDK：\n\npython -m pip install -r requirements.txt",
        "invalid_input_title": "输入无效",
        "no_results_title": "没有结果",
        "no_results_message": "请先运行一次扫描。",
        "export_title": "导出收盘结果",
        "exported_title": "已导出",
        "exported_message": "已保存 {count} 行。",
        "scan_failed_title": "扫描失败",
        "no_symbols_message": "没有可扫描的股票。请输入代码，或清空代码框以扫描美股股票池。",
        "no_sector_message": "请先选择板块。点击“加载板块”，选择一个板块后再扫描。",
        "dir_any": "不限",
        "dir_gainers": "上涨",
        "dir_losers": "下跌",
        "match_any": "任意选中特征",
        "match_all": "全部选中特征",
    },
}


@dataclass
class ScannerConfig:
    host: str
    port: int
    source_mode: str
    manual_symbols: list[str]
    sector_type: str
    sector_code: str
    sector_label: str
    max_symbols: int
    batch_size: int
    min_after_volume: float
    min_after_turnover: float
    min_abs_after_change_rate: float
    min_after_price: float
    max_after_price: float
    min_after_amplitude: float
    direction: str
    sort_by: str
    only_active_after_hours: bool
    selected_traits: set[str]
    match_mode: str
    max_technical_checks: int
    history_candles: int
    mover_ratio_threshold: float
    min_market_cap: float
    min_liquidity_turnover: float
    liquidity_days: int
    min_mover_turnover: float
    min_breakout_turnover: float
    breakout_turnover_multiple: float
    min_trait_price: float
    min_day_gain_rate: float
    box_days: int
    box_width_pct: float
    ema_convergence_pct: float
    ema_bullish_days: int
    near_ema_pct: float


def parse_symbols(raw: str) -> list[str]:
    symbols: list[str] = []
    for piece in raw.replace("\n", ",").replace(" ", ",").split(","):
        symbol = piece.strip().upper()
        if not symbol:
            continue
        if "." not in symbol:
            symbol = f"US.{symbol}"
        symbols.append(symbol)
    return list(dict.fromkeys(symbols))


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_number(value):
    num = to_float(value, default=0.0)
    if abs(num) < 1e-12:
        return ""
    if abs(num) >= 1_000_000:
        return f"{num:,.0f}"
    if abs(num) >= 1_000:
        return f"{num:,.2f}"
    return f"{num:.4f}".rstrip("0").rstrip(".")


def clean_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def percent_distance(value: float, reference: float) -> float:
    if value <= 0 or reference <= 0:
        return float("inf")
    return abs(value - reference) / reference * 100


def choose_scan_price(row: dict) -> float:
    return to_float(row.get("last_price"))


def compute_day_change_rate(row: dict) -> float:
    price = to_float(row.get("scan_price")) or choose_scan_price(row)
    prev_close = to_float(row.get("prev_close_price"))
    if price > 0 and prev_close > 0:
        return (price - prev_close) / prev_close * 100
    return to_float(row.get("change_rate"))


def compute_gap_pct(row: dict) -> float:
    open_price = to_float(row.get("open_price"))
    prev_close = to_float(row.get("prev_close_price"))
    if open_price > 0 and prev_close > 0:
        return (open_price - prev_close) / prev_close * 100
    return 0.0


def enrich_snapshot_row(row: dict) -> dict:
    row["scan_price"] = choose_scan_price(row)
    row["day_change_rate"] = compute_day_change_rate(row)
    row["gap_pct"] = compute_gap_pct(row)
    row["total_turnover_scan"] = to_float(row.get("turnover"))
    row.setdefault("volume_ratio", "")
    row.setdefault("match_count", 0)
    row.setdefault("matched_traits", "")
    row.setdefault("_matched_trait_keys", [])
    row.setdefault("box_high_20", "")
    row.setdefault("box_low_20", "")
    row.setdefault("box_width_pct", "")
    row.setdefault("breakout_side", "")
    row.setdefault("ema5", "")
    row.setdefault("ema10", "")
    row.setdefault("ema20", "")
    row.setdefault("ema50", "")
    row.setdefault("ema200", "")
    row.setdefault("near_ema", "")
    return row


def dataframe_rows(dataframe) -> list[dict]:
    rows: list[dict] = []
    if dataframe is None or getattr(dataframe, "empty", True):
        return rows

    for _, item in dataframe.iterrows():
        row = {}
        for column in getattr(dataframe, "columns", []):
            row[column] = item[column]
        for column in SNAPSHOT_COLUMNS:
            row.setdefault(column, "")
        rows.append(enrich_snapshot_row(row))
    return rows


def normalize_history(dataframe):
    if pd is None or dataframe is None or getattr(dataframe, "empty", True):
        return None

    daily = dataframe.copy()
    for column in ["open", "close", "high", "low", "volume", "turnover", "change_rate"]:
        if column not in daily.columns:
            daily[column] = 0.0
        daily[column] = daily[column].apply(to_float)

    if "time_key" not in daily.columns:
        return None

    daily["dt"] = pd.to_datetime(daily["time_key"], errors="coerce")
    daily = daily.dropna(subset=["dt"]).sort_values("dt")
    daily = daily[daily["close"] > 0]
    if daily.empty:
        return None

    for span in [5, 10, 20, 50, 200]:
        daily[f"ema{span}"] = daily["close"].ewm(span=span, adjust=False).mean()

    return daily


def make_weekly_history(daily):
    if pd is None or daily is None or daily.empty:
        return None

    weekly = (
        daily.set_index("dt")
        .resample("W-FRI")
        .agg(
            {
                "close": "last",
                "high": "max",
                "low": "min",
                "volume": "sum",
                "turnover": "sum",
            }
        )
        .dropna()
    )
    if weekly.empty:
        return None

    for span in [5, 10, 20]:
        weekly[f"ema{span}"] = weekly["close"].ewm(span=span, adjust=False).mean()

    return weekly


def is_ema_bullish(record) -> bool:
    return to_float(record.get("ema5")) > to_float(record.get("ema10")) > to_float(record.get("ema20"))


def is_ema_converged(record, threshold_pct: float) -> bool:
    ema_values = [to_float(record.get("ema5")), to_float(record.get("ema10")), to_float(record.get("ema20"))]
    if min(ema_values) <= 0:
        return False
    avg_ema = sum(ema_values) / len(ema_values)
    spread_pct = (max(ema_values) - min(ema_values)) / avg_ema * 100
    return spread_pct <= threshold_pct


def are_emas_flat_or_rising(daily, spans: list[int], lookback_days: int) -> bool:
    if len(daily) < lookback_days:
        return False
    start = daily.tail(lookback_days).iloc[0]
    latest = daily.iloc[-1]
    for span in spans:
        if to_float(latest.get(f"ema{span}")) < to_float(start.get(f"ema{span}")):
            return False
    return True


def has_tight_ema_cluster(daily, threshold_pct: float, lookback_days: int) -> bool:
    if len(daily) < lookback_days:
        return False
    recent = daily.tail(lookback_days)
    return all(is_ema_converged(item, threshold_pct) for _, item in recent.iterrows())


def is_ema_rising(daily, span: int, lookback_days: int) -> bool:
    if len(daily) < lookback_days:
        return False
    start = to_float(daily.tail(lookback_days).iloc[0].get(f"ema{span}"))
    latest = to_float(daily.iloc[-1].get(f"ema{span}"))
    return latest > 0 and latest >= start


def near_rising_ema(row: dict, daily, span: int, config: ScannerConfig) -> str:
    latest = daily.iloc[-1]
    price = to_float(row.get("scan_price")) or to_float(latest.get("close"))
    ema_value = to_float(latest.get(f"ema{span}"))
    distance = percent_distance(price, ema_value)
    if distance <= config.near_ema_pct and is_ema_rising(daily, span, config.ema_bullish_days):
        return f"EMA{span} {distance:.2f}%"
    return ""


def market_cap_ok(row: dict, config: ScannerConfig) -> bool:
    if config.min_market_cap <= 0:
        return True
    return to_float(row.get("total_market_val")) >= config.min_market_cap


def recent_turnover_floor_ok(daily, days: int, min_turnover: float) -> bool:
    if min_turnover <= 0:
        return True
    if len(daily) < days:
        return False
    recent = daily.tail(days)
    return bool((recent["turnover"].apply(to_float) >= min_turnover).all())


def latest_turnover_ok(row: dict, daily, config: ScannerConfig) -> bool:
    if config.min_liquidity_turnover <= 0:
        return True
    latest_turnover = max(
        to_float(row.get("total_turnover_scan")),
        to_float(row.get("turnover")),
        to_float(daily.iloc[-1].get("turnover")),
    )
    return latest_turnover >= config.min_liquidity_turnover


def mover_trait_ok(row: dict, config: ScannerConfig, turnover: float | None = None, mover_ratio: float | None = None) -> bool:
    price = to_float(row.get("scan_price"))
    turnover_value = max(
        to_float(row.get("total_turnover_scan")),
        to_float(row.get("turnover")),
    ) if turnover is None else turnover
    mover_ratio_value = to_float(row.get("volume_ratio")) if mover_ratio is None else mover_ratio
    day_change_rate = to_float(row.get("day_change_rate"))
    return (
        price >= config.min_trait_price
        and abs(day_change_rate) >= config.min_day_gain_rate
        and mover_ratio_value >= config.mover_ratio_threshold
        and turnover_value >= config.min_mover_turnover
    )


def possible_volume_surge(row: dict, config: ScannerConfig) -> bool:
    if TRAIT_VOLUME_SURGE not in config.selected_traits:
        return False
    if TRAIT_VOLUME_SURGE in (row.get("_matched_trait_keys") or []):
        return False
    price = to_float(row.get("scan_price"))
    turnover = max(to_float(row.get("total_turnover_scan")), to_float(row.get("turnover")))
    mover_ratio = to_float(row.get("volume_ratio"))
    day_change_rate = to_float(row.get("day_change_rate"))
    return (
        price >= config.min_trait_price
        and abs(day_change_rate) >= config.min_day_gain_rate
        and mover_ratio >= config.mover_ratio_threshold
        and (config.min_mover_turnover <= 0 or turnover == 0 or turnover >= config.min_mover_turnover)
    )


def finalize_trait_fields(row: dict, matched: list[str], config: ScannerConfig) -> dict:
    selected_count = len(config.selected_traits)
    matched_keys = []
    for key in TRAIT_LABELS:
        if key in config.selected_traits and key in matched and key not in matched_keys:
            matched_keys.append(key)

    match_count = len(matched_keys)
    row["match_count"] = match_count
    row["_matched_trait_keys"] = matched_keys
    row["matched_traits"] = ", ".join(TRAIT_LABELS[key] for key in matched_keys)

    if selected_count == 0:
        row["_trait_pass"] = True
    elif config.match_mode == "All Selected":
        row["_trait_pass"] = match_count == selected_count
    else:
        row["_trait_pass"] = match_count > 0

    return row


def add_snapshot_traits(row: dict, config: ScannerConfig) -> dict:
    matched = list(row.get("_matched_trait_keys") or [])
    if TRAIT_VOLUME_SURGE in config.selected_traits:
        if mover_trait_ok(row, config):
            matched.append(TRAIT_VOLUME_SURGE)

    return finalize_trait_fields(row, matched, config)


def add_history_traits(row: dict, daily, config: ScannerConfig) -> dict:
    row = add_snapshot_traits(row, config)
    matched = list(row.get("_matched_trait_keys") or [])
    if daily is None or len(daily) < 25:
        return finalize_trait_fields(row, matched, config)

    latest = daily.iloc[-1]
    price = to_float(row.get("scan_price")) or to_float(latest.get("close"))
    latest_turnover = max(
        to_float(row.get("total_turnover_scan")),
        to_float(row.get("turnover")),
        to_float(latest.get("turnover")),
    )
    if not row.get("day_change_rate"):
        row["day_change_rate"] = to_float(latest.get("change_rate"))

    for span in [5, 10, 20, 50, 200]:
        row[f"ema{span}"] = to_float(latest.get(f"ema{span}"))

    if TRAIT_VOLUME_SURGE in config.selected_traits:
        if mover_trait_ok(row, config, turnover=latest_turnover):
            matched.append(TRAIT_VOLUME_SURGE)

    if TRAIT_BOX_BREAKOUT in config.selected_traits and len(daily) >= config.box_days + 1:
        prior_box = daily.iloc[-config.box_days - 1 : -1]
        box_high = to_float(prior_box["high"].max())
        box_low = to_float(prior_box["low"].min())
        box_width_pct = (box_high / box_low - 1) * 100 if box_high > 0 and box_low > 0 else float("inf")
        row["box_high_20"] = box_high
        row["box_low_20"] = box_low
        row["box_width_pct"] = box_width_pct
        previous_five = daily.iloc[-6:-1] if len(daily) >= 6 else daily.iloc[:-1]
        avg_turnover_5 = to_float(previous_five["turnover"].mean()) if not previous_five.empty else 0
        breakout_side = ""
        if price > box_high:
            breakout_side = "Up"
        elif price < box_low:
            breakout_side = "Down"
        row["breakout_side"] = breakout_side
        if (
            breakout_side
            and box_width_pct <= config.box_width_pct
            and market_cap_ok(row, config)
            and avg_turnover_5 > 0
            and latest_turnover >= avg_turnover_5 * config.breakout_turnover_multiple
            and latest_turnover >= config.min_breakout_turnover
        ):
            matched.append(TRAIT_BOX_BREAKOUT)

    if TRAIT_EMA_CONVERGED in config.selected_traits:
        if (
            price >= config.min_trait_price
            and market_cap_ok(row, config)
            and recent_turnover_floor_ok(daily, config.liquidity_days, config.min_liquidity_turnover)
            and has_tight_ema_cluster(
                daily,
                config.ema_convergence_pct,
                config.ema_bullish_days,
            )
            and are_emas_flat_or_rising(daily, [5, 10, 20], config.ema_bullish_days)
        ):
            matched.append(TRAIT_EMA_CONVERGED)

    near_parts: list[str] = []
    for trait_key, span in [
        (TRAIT_NEAR_EMA20, 20),
        (TRAIT_NEAR_EMA50, 50),
        (TRAIT_NEAR_EMA200, 200),
    ]:
        if trait_key not in config.selected_traits:
            continue
        near_text = near_rising_ema(row, daily, span, config)
        if (
            near_text
            and price >= config.min_trait_price
            and market_cap_ok(row, config)
            and latest_turnover_ok(row, daily, config)
        ):
            near_parts.append(near_text)
            matched.append(trait_key)
    row["near_ema"] = ", ".join(near_parts)

    return finalize_trait_fields(row, matched, config)


class AfterHoursScannerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Futu Close Pattern Scanner")
        self.geometry("1380x820")
        self.minsize(1120, 680)
        self.configure(bg=APP_BG)
        self.option_add("*Font", FONT_BODY)

        self.results: list[dict] = []
        self.worker: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.language = "en"
        self.i18n_widgets: dict[str, list[tk.Widget]] = {}
        self.trait_checkbuttons: dict[str, ttk.Checkbutton] = {}
        self.notebook: ttk.Notebook | None = None
        self.scan_tab = None
        self.traits_tab = None
        self.direction_combo: ttk.Combobox | None = None
        self.match_mode_combo: ttk.Combobox | None = None
        self.source_combo: ttk.Combobox | None = None
        self.sector_type_combo: ttk.Combobox | None = None
        self.sector_combo: ttk.Combobox | None = None
        self.load_sectors_button: ttk.Button | None = None
        self.sector_lookup: dict[str, str] = {}
        self.sectors_loading = False
        self.scan_canvas: tk.Canvas | None = None
        self.traits_canvas: tk.Canvas | None = None
        self.active_scroll_canvas: tk.Canvas | None = None

        self._configure_styles()
        self._build_ui()
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.after(100, self._poll_messages)

    def tr(self, key: str, **kwargs) -> str:
        text = UI_TEXT.get(self.language, UI_TEXT["en"]).get(key, UI_TEXT["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def trait_label(self, key: str) -> str:
        return TRAIT_LABELS_BY_LANG.get(self.language, TRAIT_LABELS_BY_LANG["en"]).get(key, key)

    def column_label(self, key: str) -> str:
        return COLUMN_LABELS_BY_LANG.get(self.language, COLUMN_LABELS_BY_LANG["en"]).get(key, key)

    def register_text(self, widget: tk.Widget, key: str) -> tk.Widget:
        self.i18n_widgets.setdefault(key, []).append(widget)
        widget.configure(text=self.tr(key))
        return widget

    def ui_label(self, parent, key: str, **kwargs) -> ttk.Label:
        style = kwargs.pop("style", None)
        label = ttk.Label(parent, style=style) if style else ttk.Label(parent)
        self.register_text(label, key)
        label.grid(**kwargs)
        return label

    def ui_button(self, parent, key: str, command, **kwargs) -> ttk.Button:
        style = kwargs.pop("style", None)
        button = ttk.Button(parent, command=command, style=style) if style else ttk.Button(parent, command=command)
        self.register_text(button, key)
        button.grid(**kwargs)
        return button

    def direction_internal(self) -> str:
        value = self.direction_var.get()
        options = {
            self.tr("dir_any"): "Any",
            self.tr("dir_gainers"): "Gainers",
            self.tr("dir_losers"): "Losers",
            "Any": "Any",
            "Gainers": "Gainers",
            "Losers": "Losers",
            "不限": "Any",
            "上涨": "Gainers",
            "下跌": "Losers",
        }
        return options.get(value, "Any")

    def source_internal(self) -> str:
        value = self.source_mode_var.get()
        options = {
            self.tr("source_manual"): "Manual Symbols",
            self.tr("source_universe"): "U.S. Stock Universe",
            self.tr("source_sector"): "Sector Stocks",
            "Manual Symbols": "Manual Symbols",
            "U.S. Stock Universe": "U.S. Stock Universe",
            "Sector Stocks": "Sector Stocks",
            "手动代码": "Manual Symbols",
            "美股全市场": "U.S. Stock Universe",
            "板块股票": "Sector Stocks",
        }
        return options.get(value, "Manual Symbols")

    def sector_type_internal(self) -> str:
        value = self.sector_type_var.get()
        options = {
            self.tr("sector_industry"): "INDUSTRY",
            self.tr("sector_concept"): "CONCEPT",
            self.tr("sector_region"): "REGION",
            self.tr("sector_other"): "OTHER",
            self.tr("sector_all"): "ALL",
            "Industry": "INDUSTRY",
            "Concept": "CONCEPT",
            "Region": "REGION",
            "Other": "OTHER",
            "All": "ALL",
            "行业": "INDUSTRY",
            "概念": "CONCEPT",
            "地区": "REGION",
            "其他": "OTHER",
            "全部": "ALL",
        }
        return options.get(value, "INDUSTRY")

    def match_mode_internal(self) -> str:
        value = self.match_mode_var.get()
        options = {
            self.tr("match_any"): "Any Selected",
            self.tr("match_all"): "All Selected",
            "Any Selected": "Any Selected",
            "All Selected": "All Selected",
            "任意选中特征": "Any Selected",
            "全部选中特征": "All Selected",
        }
        return options.get(value, "Any Selected")

    def set_direction_display(self, internal: str) -> None:
        labels = {
            "Any": self.tr("dir_any"),
            "Gainers": self.tr("dir_gainers"),
            "Losers": self.tr("dir_losers"),
        }
        self.direction_var.set(labels.get(internal, labels["Any"]))

    def set_source_display(self, internal: str) -> None:
        labels = {
            "Manual Symbols": self.tr("source_manual"),
            "U.S. Stock Universe": self.tr("source_universe"),
            "Sector Stocks": self.tr("source_sector"),
        }
        self.source_mode_var.set(labels.get(internal, labels["Manual Symbols"]))

    def update_source_controls(self, *_event) -> None:
        source_mode = self.source_internal()
        manual_enabled = source_mode == "Manual Symbols"
        sector_enabled = source_mode == "Sector Stocks"

        if hasattr(self, "symbol_text"):
            self.symbol_text.configure(state="normal" if manual_enabled else "disabled")
        if self.sector_type_combo is not None:
            self.sector_type_combo.configure(state="readonly" if sector_enabled else "disabled")
        if self.sector_combo is not None:
            self.sector_combo.configure(state="readonly" if sector_enabled else "disabled")
        if self.load_sectors_button is not None:
            state = "normal" if sector_enabled and not self.sectors_loading else "disabled"
            self.load_sectors_button.configure(state=state)

    def set_sector_type_display(self, internal: str) -> None:
        labels = {
            "INDUSTRY": self.tr("sector_industry"),
            "CONCEPT": self.tr("sector_concept"),
            "REGION": self.tr("sector_region"),
            "OTHER": self.tr("sector_other"),
            "ALL": self.tr("sector_all"),
        }
        self.sector_type_var.set(labels.get(internal, labels["INDUSTRY"]))

    def set_match_mode_display(self, internal: str) -> None:
        labels = {
            "Any Selected": self.tr("match_any"),
            "All Selected": self.tr("match_all"),
        }
        self.match_mode_var.set(labels.get(internal, labels["Any Selected"]))

    def apply_language(self) -> None:
        for key, widgets in self.i18n_widgets.items():
            for widget in widgets:
                widget.configure(text=self.tr(key))

        if self.notebook is not None:
            self.notebook.tab(self.scan_tab, text=self.tr("tab_scan"))
            self.notebook.tab(self.traits_tab, text=self.tr("tab_traits"))

        for key, widget in self.trait_checkbuttons.items():
            widget.configure(text=self.trait_label(key))

        if self.direction_combo is not None:
            self.direction_combo.configure(
                values=[self.tr("dir_any"), self.tr("dir_gainers"), self.tr("dir_losers")]
            )
        if self.match_mode_combo is not None:
            self.match_mode_combo.configure(values=[self.tr("match_any"), self.tr("match_all")])
        if self.source_combo is not None:
            self.source_combo.configure(
                values=[self.tr("source_manual"), self.tr("source_universe"), self.tr("source_sector")]
            )
        if self.sector_type_combo is not None:
            self.sector_type_combo.configure(
                values=[
                    self.tr("sector_industry"),
                    self.tr("sector_concept"),
                    self.tr("sector_region"),
                    self.tr("sector_other"),
                    self.tr("sector_all"),
                ]
            )

        if hasattr(self, "tree"):
            for column in DISPLAY_COLUMNS:
                self.tree.heading(column, text=self.column_label(column))
            self._refresh_table()
        self.update_source_controls()

    def toggle_language(self) -> None:
        direction = self.direction_internal()
        match_mode = self.match_mode_internal()
        source_mode = self.source_internal()
        sector_type = self.sector_type_internal()
        self.language = "zh" if self.language == "en" else "en"
        self.set_direction_display(direction)
        self.set_match_mode_display(match_mode)
        self.set_source_display(source_mode)
        self.set_sector_type_display(sector_type)
        self.apply_language()
        if not self.results:
            self.status_var.set(self.tr("status_initial"))

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", font=FONT_BODY, background=APP_BG, foreground=TEXT)
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Card.TFrame", background=PANEL_ALT)
        style.configure("TLabel", background=PANEL_BG, foreground=TEXT, font=FONT_BODY)
        style.configure("Panel.TLabel", background=PANEL_BG, foreground=TEXT, font=FONT_BODY)
        style.configure("Card.TLabel", background=PANEL_ALT, foreground=TEXT, font=FONT_BODY)
        style.configure("Muted.TLabel", background=APP_BG, foreground=MUTED, font=FONT_SMALL)
        style.configure("PanelMuted.TLabel", background=PANEL_BG, foreground=MUTED, font=FONT_SMALL)
        style.configure("CardMuted.TLabel", background=PANEL_ALT, foreground=MUTED, font=FONT_SMALL)
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT, font=FONT_TITLE)
        style.configure("Brand.TLabel", background=PANEL_BG, foreground=TEXT, font=FONT_TITLE)
        style.configure("Section.TLabel", background=PANEL_BG, foreground=TEXT, font=FONT_SECTION)
        style.configure(
            "TEntry",
            fieldbackground=FIELD_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(8, 6),
        )
        style.configure(
            "TCombobox",
            fieldbackground=FIELD_BG,
            background=FIELD_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            arrowcolor=MUTED,
            padding=(8, 6),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", FIELD_BG)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", FIELD_BG)],
            selectforeground=[("readonly", TEXT)],
        )
        style.configure(
            "TCheckbutton",
            background=PANEL_BG,
            foreground=TEXT,
            indicatorbackground=FIELD_BG,
            indicatorforeground=ACCENT,
            focuscolor=PANEL_BG,
        )
        style.map(
            "TCheckbutton",
            background=[("active", PANEL_BG)],
            foreground=[("disabled", MUTED), ("active", TEXT)],
        )
        style.configure(
            "TButton",
            background=PANEL_ALT,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(12, 8),
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("disabled", "#202533"), ("pressed", "#252b3a"), ("active", "#252b3a")],
            foreground=[("disabled", MUTED), ("active", TEXT)],
        )
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#07110e",
            bordercolor=ACCENT,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
            padding=(12, 8),
        )
        style.map(
            "Accent.TButton",
            background=[("disabled", "#234238"), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
            foreground=[("disabled", MUTED), ("active", "#07110e")],
        )
        style.configure("Horizontal.TProgressbar", troughcolor=FIELD_BG, background=ACCENT, bordercolor=BORDER)
        style.configure("TSeparator", background=BORDER)
        for scrollbar_style in ["Modern.Vertical.TScrollbar", "Modern.Horizontal.TScrollbar"]:
            style.configure(
                scrollbar_style,
                background=PANEL_ALT,
                darkcolor=PANEL_ALT,
                lightcolor=PANEL_ALT,
                troughcolor=FIELD_BG,
                bordercolor=FIELD_BG,
                arrowcolor=MUTED,
                relief="flat",
                gripcount=0,
                arrowsize=12,
                width=14,
            )
            style.map(
                scrollbar_style,
                background=[("active", "#252b3a"), ("pressed", "#30384a")],
                arrowcolor=[("active", TEXT), ("pressed", TEXT)],
            )
        style.configure("TNotebook", background=PANEL_BG, borderwidth=0, tabmargins=(0, 8, 0, 0))
        style.configure(
            "TNotebook.Tab",
            background=PANEL_BG,
            foreground=MUTED,
            padding=(14, 8),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PANEL_ALT), ("active", PANEL_ALT)],
            foreground=[("selected", TEXT), ("active", TEXT)],
        )
        style.configure(
            "Treeview",
            background=FIELD_BG,
            fieldbackground=FIELD_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            rowheight=30,
            font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=PANEL_ALT,
            foreground=MUTED,
            bordercolor=BORDER,
            relief="flat",
            font=FONT_SECTION,
            padding=(8, 8),
        )
        style.map(
            "Treeview",
            background=[("selected", "#20362f")],
            foreground=[("selected", TEXT)],
        )

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, padding=(16, 16, 12, 16), style="Panel.TFrame")
        controls.grid(row=0, column=0, sticky="ns")
        controls.rowconfigure(3, weight=1)
        controls.columnconfigure(0, weight=1)

        self.ui_label(controls, "app_brand", style="Brand.TLabel", row=0, column=0, sticky="w")
        self.ui_label(
            controls,
            "app_subtitle",
            style="PanelMuted.TLabel",
            row=1,
            column=0,
            sticky="w",
            pady=(2, 10),
        )
        ttk.Separator(controls).grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.notebook = ttk.Notebook(controls, width=350)
        self.notebook.grid(row=3, column=0, sticky="nsew")

        self.scan_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.traits_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.scan_tab, text=self.tr("tab_scan"))
        self.notebook.add(self.traits_tab, text=self.tr("tab_traits"))

        actions = ttk.Frame(controls, padding=(0, 12, 0, 0), style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        results_frame = ttk.Frame(self, padding=(18, 18, 18, 18), style="App.TFrame")
        results_frame.grid(row=0, column=1, sticky="nsew")
        results_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)

        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="11111")
        self.max_symbols_var = tk.StringVar(value="8000")
        self.batch_size_var = tk.StringVar(value="300")
        self.min_after_volume_var = tk.StringVar(value="0")
        self.min_after_turnover_var = tk.StringVar(value="0")
        self.min_abs_after_change_rate_var = tk.StringVar(value="0")
        self.min_after_price_var = tk.StringVar(value="0")
        self.max_after_price_var = tk.StringVar(value="0")
        self.min_after_amplitude_var = tk.StringVar(value="0")
        self.source_mode_var = tk.StringVar(value=self.tr("source_universe"))
        self.sector_type_var = tk.StringVar(value=self.tr("sector_industry"))
        self.sector_var = tk.StringVar(value="")
        self.direction_var = tk.StringVar(value=self.tr("dir_any"))
        self.sort_by_var = tk.StringVar(value="match_count")
        self.only_active_after_hours_var = tk.BooleanVar(value=True)

        self.trait_vars = {
            TRAIT_VOLUME_SURGE: tk.BooleanVar(value=True),
            TRAIT_BOX_BREAKOUT: tk.BooleanVar(value=True),
            TRAIT_EMA_CONVERGED: tk.BooleanVar(value=True),
            TRAIT_NEAR_EMA20: tk.BooleanVar(value=True),
            TRAIT_NEAR_EMA50: tk.BooleanVar(value=True),
            TRAIT_NEAR_EMA200: tk.BooleanVar(value=True),
        }
        self.match_mode_var = tk.StringVar(value=self.tr("match_any"))
        self.max_technical_checks_var = tk.StringVar(value="80")
        self.history_candles_var = tk.StringVar(value="260")
        self.mover_ratio_threshold_var = tk.StringVar(value="2")
        self.min_market_cap_var = tk.StringVar(value="500000000")
        self.min_liquidity_turnover_var = tk.StringVar(value="10000000")
        self.liquidity_days_var = tk.StringVar(value="20")
        self.min_mover_turnover_var = tk.StringVar(value="50000000")
        self.min_breakout_turnover_var = tk.StringVar(value="30000000")
        self.breakout_turnover_multiple_var = tk.StringVar(value="1.5")
        self.min_trait_price_var = tk.StringVar(value="3")
        self.min_day_gain_rate_var = tk.StringVar(value="10")
        self.box_days_var = tk.StringVar(value="20")
        self.box_width_pct_var = tk.StringVar(value="15")
        self.ema_convergence_pct_var = tk.StringVar(value="3")
        self.ema_bullish_days_var = tk.StringVar(value="5")
        self.near_ema_pct_var = tk.StringVar(value="3")

        scan_content, self.scan_canvas = self._make_scrollable_tab(self.scan_tab)
        traits_content, self.traits_canvas = self._make_scrollable_tab(self.traits_tab)
        self._build_scan_tab(scan_content)
        self._build_traits_tab(traits_content)
        self._build_action_bar(actions)
        self._build_results(results_frame)
        self.update_source_controls()

    def _make_scrollable_tab(self, parent) -> tuple[ttk.Frame, tk.Canvas]:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        canvas = tk.Canvas(
            parent,
            bg=PANEL_BG,
            highlightthickness=0,
            borderwidth=0,
            yscrollincrement=24,
        )
        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=canvas.yview,
            style="Modern.Vertical.TScrollbar",
        )
        content = ttk.Frame(canvas, padding=(10, 12), style="Panel.TFrame")
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def sync_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", sync_scroll_region)
        canvas.bind("<Configure>", sync_width)
        canvas.bind("<Enter>", lambda _event: setattr(self, "active_scroll_canvas", canvas))
        canvas.bind("<Leave>", lambda _event: setattr(self, "active_scroll_canvas", None))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return content, canvas

    def _on_mousewheel(self, event) -> None:
        if self.active_scroll_canvas is not None:
            self.active_scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_scan_tab(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0

        self.ui_label(parent, "section_connection", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        self.ui_label(parent, "opend_host", row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.host_var, width=18).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        self.ui_label(parent, "opend_port", row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.port_var, width=18).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=12)
        row += 1

        self.ui_label(parent, "section_universe", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        self.ui_label(parent, "source", row=row, column=0, sticky="w")
        self.source_combo = ttk.Combobox(
            parent,
            textvariable=self.source_mode_var,
            values=[self.tr("source_manual"), self.tr("source_universe"), self.tr("source_sector")],
            state="readonly",
        )
        self.source_combo.bind("<<ComboboxSelected>>", self.update_source_controls)
        self.source_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        self.ui_label(parent, "symbols", row=row, column=0, sticky="nw")
        self.symbol_text = tk.Text(parent, width=28, height=7, wrap="word")
        self.symbol_text.grid(row=row, column=1, sticky="ew", pady=2)
        self.symbol_text.insert("1.0", "AAPL, TSLA, NVDA, MSFT")
        self.symbol_text.configure(
            bg=FIELD_BG,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#20362f",
            selectforeground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            padx=8,
            pady=8,
        )
        row += 1

        self.ui_label(parent, "sector_type", row=row, column=0, sticky="w")
        self.sector_type_combo = ttk.Combobox(
            parent,
            textvariable=self.sector_type_var,
            values=[
                self.tr("sector_industry"),
                self.tr("sector_concept"),
                self.tr("sector_region"),
                self.tr("sector_other"),
                self.tr("sector_all"),
            ],
            state="readonly",
        )
        self.sector_type_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        self.load_sectors_button = self.ui_button(
            parent,
            "load_sectors",
            command=self.load_sectors,
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=3,
        )
        row += 1

        self.ui_label(parent, "sector", row=row, column=0, sticky="w")
        self.sector_combo = ttk.Combobox(
            parent,
            textvariable=self.sector_var,
            values=[],
            state="readonly",
        )
        self.sector_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        self.ui_label(parent, "max_symbols", row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.max_symbols_var).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        self.ui_label(parent, "batch_size", row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.batch_size_var).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=12)
        row += 1

        self.ui_label(parent, "section_after_filters", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        filters = [
            ("min_ah_turnover", self.min_after_turnover_var),
            ("min_abs_ah_pct", self.min_abs_after_change_rate_var),
            ("min_ah_price", self.min_after_price_var),
            ("max_ah_price", self.max_after_price_var),
            ("min_ah_amplitude", self.min_after_amplitude_var),
        ]
        for label_key, variable in filters:
            self.ui_label(parent, label_key, row=row, column=0, sticky="w")
            ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
            row += 1

        self.ui_label(parent, "direction", row=row, column=0, sticky="w")
        self.direction_combo = ttk.Combobox(
            parent,
            textvariable=self.direction_var,
            values=[self.tr("dir_any"), self.tr("dir_gainers"), self.tr("dir_losers")],
            state="readonly",
        )
        self.direction_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        self.ui_label(parent, "sort_by", row=row, column=0, sticky="w")
        ttk.Combobox(
            parent,
            textvariable=self.sort_by_var,
            values=[
                "match_count",
                "day_change_rate",
                "gap_pct",
                "volume_ratio",
                "volume",
                "turnover",
                "turnover_rate",
                "amplitude",
                "box_width_pct",
                "scan_price",
                "total_market_val",
            ],
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        active_after_hours_checkbox = ttk.Checkbutton(
            parent,
            variable=self.only_active_after_hours_var,
            text=self.tr("only_active_after_hours"),
        )
        active_after_hours_checkbox.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 12))
        self.register_text(active_after_hours_checkbox, "only_active_after_hours")
        row += 1

    def _build_traits_tab(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0

        self.ui_label(parent, "section_technical_traits", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        for key in [
            TRAIT_VOLUME_SURGE,
            TRAIT_BOX_BREAKOUT,
            TRAIT_EMA_CONVERGED,
            TRAIT_NEAR_EMA20,
            TRAIT_NEAR_EMA50,
            TRAIT_NEAR_EMA200,
        ]:
            checkbox = ttk.Checkbutton(parent, variable=self.trait_vars[key], text=self.trait_label(key))
            checkbox.grid(
                row=row,
                column=0,
                columnspan=2,
                sticky="w",
                pady=3,
            )
            self.trait_checkbuttons[key] = checkbox
            row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=12)
        row += 1

        self.ui_label(parent, "section_matching", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        self.ui_label(parent, "match_mode", row=row, column=0, sticky="w")
        self.match_mode_combo = ttk.Combobox(
            parent,
            textvariable=self.match_mode_var,
            values=[self.tr("match_any"), self.tr("match_all")],
            state="readonly",
        )
        self.match_mode_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=12)
        row += 1

        self.ui_label(parent, "section_thresholds", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        fields = [
            ("max_tech_checks", self.max_technical_checks_var),
            ("history_candles", self.history_candles_var),
            ("min_mover_ratio", self.mover_ratio_threshold_var),
            ("min_mover_turnover", self.min_mover_turnover_var),
            ("min_breakout_turnover", self.min_breakout_turnover_var),
            ("min_market_cap", self.min_market_cap_var),
            ("min_liquidity_turnover", self.min_liquidity_turnover_var),
            ("liquidity_days", self.liquidity_days_var),
            ("breakout_turnover_multiple", self.breakout_turnover_multiple_var),
            ("min_price", self.min_trait_price_var),
            ("min_day_gain_pct", self.min_day_gain_rate_var),
            ("box_days", self.box_days_var),
            ("max_box_width_pct", self.box_width_pct_var),
            ("ema_tight_pct", self.ema_convergence_pct_var),
            ("ema_bull_days", self.ema_bullish_days_var),
            ("near_ema_pct", self.near_ema_pct_var),
        ]
        for label_key, variable in fields:
            self.ui_label(parent, label_key, row=row, column=0, sticky="w")
            ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
            row += 1

        self.ui_button(parent, "dad_preset", command=self.apply_dad_preset, style="Accent.TButton", row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _build_action_bar(self, parent) -> None:
        self.scan_button = self.ui_button(parent, "scan", command=self.start_scan, style="Accent.TButton", row=0, column=0, sticky="ew", pady=3, padx=(0, 4))
        self.stop_button = self.ui_button(parent, "stop", command=self.stop_scan, row=0, column=1, sticky="ew", pady=3, padx=(4, 0))
        self.stop_button.configure(state="disabled")
        self.ui_button(parent, "export_csv", command=self.export_csv, row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _build_results(self, parent) -> None:
        header = ttk.Frame(parent, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        self.ui_label(header, "results_title", style="Title.TLabel", row=0, column=0, sticky="w")
        self.ui_label(
            header,
            "results_subtitle",
            style="Muted.TLabel",
            row=1,
            column=0,
            sticky="w",
            pady=(3, 0),
        )

        status_panel = ttk.Frame(parent, padding=(14, 12), style="Card.TFrame")
        status_panel.grid(row=1, column=0, sticky="ew", pady=(16, 10))
        status_panel.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value=self.tr("status_initial"))
        ttk.Label(status_panel, textvariable=self.status_var, style="CardMuted.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.progress = ttk.Progressbar(status_panel, mode="determinate", length=300)
        self.progress.grid(row=0, column=1, sticky="e", padx=(14, 0))

        table_frame = ttk.Frame(parent, padding=1, style="Card.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=DISPLAY_COLUMNS, show="headings")
        for column in DISPLAY_COLUMNS:
            self.tree.heading(column, text=self.column_label(column))
            width = 110
            if column in {"code", "name"}:
                width = 120
            elif column == "update_time":
                width = 155
            elif column == "matched_traits":
                width = 310
            elif column == "near_ema":
                width = 170
            elif column == "breakout_side":
                width = 100
            self.tree.column(column, width=width, minwidth=80, anchor="e")
        for column in ["code", "name", "update_time", "matched_traits", "breakout_side", "near_ema"]:
            self.tree.column(column, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Modern.Vertical.TScrollbar",
        )
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
            style="Modern.Horizontal.TScrollbar",
        )
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.tag_configure("gain", foreground=GAIN)
        self.tree.tag_configure("loss", foreground=LOSS)
        self.tree.tag_configure("neutral", foreground=TEXT)

        footer = ttk.Frame(parent, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        self.ui_button(footer, "language_button", command=self.toggle_language, row=0, column=1, sticky="e")

    def apply_dad_preset(self) -> None:
        for variable in self.trait_vars.values():
            variable.set(True)
        self.set_match_mode_display("Any Selected")
        self.max_technical_checks_var.set("80")
        self.history_candles_var.set("260")
        self.mover_ratio_threshold_var.set("2")
        self.min_market_cap_var.set("500000000")
        self.min_liquidity_turnover_var.set("10000000")
        self.liquidity_days_var.set("20")
        self.min_mover_turnover_var.set("50000000")
        self.min_breakout_turnover_var.set("30000000")
        self.breakout_turnover_multiple_var.set("1.5")
        self.min_trait_price_var.set("3")
        self.min_day_gain_rate_var.set("10")
        self.box_days_var.set("20")
        self.box_width_pct_var.set("15")
        self.ema_convergence_pct_var.set("3")
        self.ema_bullish_days_var.set("5")
        self.near_ema_pct_var.set("3")

    def load_sectors(self) -> None:
        if self.source_internal() != "Sector Stocks":
            self.update_source_controls()
            return
        if OpenQuoteContext is None or Plate is None:
            messagebox.showerror(
                self.tr("missing_api_title"),
                self.tr("missing_api_message"),
            )
            return

        self.sectors_loading = True
        if self.load_sectors_button is not None:
            self.load_sectors_button.configure(state="disabled")
        self.status_var.set(self.tr("status_loading_sectors"))

        host = self.host_var.get().strip() or "127.0.0.1"
        port = int(self.port_var.get())
        sector_type = self.sector_type_internal()
        threading.Thread(
            target=self._load_sectors_worker,
            args=(host, port, sector_type),
            daemon=True,
        ).start()

    def _plate_enum(self, sector_type: str):
        mapping = {
            "INDUSTRY": Plate.INDUSTRY,
            "CONCEPT": Plate.CONCEPT,
            "REGION": Plate.REGION,
            "OTHER": Plate.OTHER,
            "ALL": Plate.ALL,
        }
        return mapping.get(sector_type, Plate.INDUSTRY)

    def _load_sectors_worker(self, host: str, port: int, sector_type: str) -> None:
        quote_ctx = None
        try:
            quote_ctx = OpenQuoteContext(host=host, port=port)
            ret, data = quote_ctx.get_plate_list(Market.US, self._plate_enum(sector_type))
            if ret != RET_OK:
                self.messages.put(("error", str(data)))
                return
            choices: list[tuple[str, str]] = []
            for _, item in data.iterrows():
                code = clean_text(item.get("code"))
                name = clean_text(item.get("plate_name"))
                if code and name:
                    choices.append((f"{name} ({code})", code))
            choices.sort(key=lambda pair: pair[0].lower())
            self.messages.put(("sector_choices", choices))
        except Exception as exc:  # noqa: BLE001 - GUI should show API/connectivity failures.
            self.messages.put(("error", str(exc)))
        finally:
            if quote_ctx is not None:
                quote_ctx.close()

    def start_scan(self) -> None:
        if OpenQuoteContext is None or pd is None:
            messagebox.showerror(
                self.tr("missing_api_title"),
                self.tr("missing_api_message"),
            )
            return

        if self.worker and self.worker.is_alive():
            return

        try:
            config = self._read_config()
        except ValueError as exc:
            messagebox.showerror(self.tr("invalid_input_title"), str(exc))
            return

        self.results.clear()
        self._clear_table()
        self.progress["value"] = 0
        self.status_var.set(self.tr("status_connecting"))
        self.stop_event.clear()
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.worker = threading.Thread(target=self._scan_worker, args=(config,), daemon=True)
        self.worker.start()

    def stop_scan(self) -> None:
        self.stop_event.set()
        self.status_var.set(self.tr("status_stopping"))

    def export_csv(self) -> None:
        if not self.results:
            messagebox.showinfo(self.tr("no_results_title"), self.tr("no_results_message"))
            return

        path = filedialog.asksaveasfilename(
            title=self.tr("export_title"),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="futu_close_pattern_results.csv",
        )
        if not path:
            return

        with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=DISPLAY_COLUMNS)
            writer.writeheader()
            for row in self.results:
                export_row = {}
                for column in DISPLAY_COLUMNS:
                    if column == "matched_traits":
                        export_row[column] = self.localized_matched_traits(row)
                    else:
                        export_row[column] = row.get(column, "")
                writer.writerow(export_row)
        messagebox.showinfo(self.tr("exported_title"), self.tr("exported_message", count=len(self.results)))

    def _read_config(self) -> ScannerConfig:
        selected_traits = {
            key for key, variable in self.trait_vars.items() if variable.get()
        }

        port = int(self.port_var.get())
        max_symbols = max(0, int(self.max_symbols_var.get()))
        batch_size = min(400, max(1, int(self.batch_size_var.get())))
        max_technical_checks = max(0, int(self.max_technical_checks_var.get()))
        history_candles = max(60, min(600, int(self.history_candles_var.get())))
        box_days = max(5, int(self.box_days_var.get()))
        ema_bullish_days = max(1, int(self.ema_bullish_days_var.get()))
        liquidity_days = max(1, int(self.liquidity_days_var.get()))

        return ScannerConfig(
            host=self.host_var.get().strip() or "127.0.0.1",
            port=port,
            source_mode=self.source_internal(),
            manual_symbols=parse_symbols(self.symbol_text.get("1.0", "end")),
            sector_type=self.sector_type_internal(),
            sector_code=self.sector_lookup.get(self.sector_var.get(), ""),
            sector_label=self.sector_var.get(),
            max_symbols=max_symbols,
            batch_size=batch_size,
            min_after_volume=to_float(self.min_after_volume_var.get()),
            min_after_turnover=to_float(self.min_after_turnover_var.get()),
            min_abs_after_change_rate=to_float(self.min_abs_after_change_rate_var.get()),
            min_after_price=to_float(self.min_after_price_var.get()),
            max_after_price=to_float(self.max_after_price_var.get()),
            min_after_amplitude=to_float(self.min_after_amplitude_var.get()),
            direction=self.direction_internal(),
            sort_by=self.sort_by_var.get(),
            only_active_after_hours=self.only_active_after_hours_var.get(),
            selected_traits=selected_traits,
            match_mode=self.match_mode_internal(),
            max_technical_checks=max_technical_checks,
            history_candles=history_candles,
            mover_ratio_threshold=to_float(self.mover_ratio_threshold_var.get()),
            min_market_cap=to_float(self.min_market_cap_var.get()),
            min_liquidity_turnover=to_float(self.min_liquidity_turnover_var.get()),
            liquidity_days=liquidity_days,
            min_mover_turnover=to_float(self.min_mover_turnover_var.get()),
            min_breakout_turnover=to_float(self.min_breakout_turnover_var.get()),
            breakout_turnover_multiple=to_float(self.breakout_turnover_multiple_var.get()),
            min_trait_price=to_float(self.min_trait_price_var.get()),
            min_day_gain_rate=to_float(self.min_day_gain_rate_var.get()),
            box_days=box_days,
            box_width_pct=to_float(self.box_width_pct_var.get()),
            ema_convergence_pct=to_float(self.ema_convergence_pct_var.get()),
            ema_bullish_days=ema_bullish_days,
            near_ema_pct=to_float(self.near_ema_pct_var.get()),
        )

    def _scan_worker(self, config: ScannerConfig) -> None:
        quote_ctx = None
        try:
            quote_ctx = OpenQuoteContext(host=config.host, port=config.port)
            symbols = self._load_scan_symbols(quote_ctx, config)
            if config.max_symbols > 0:
                symbols = symbols[: config.max_symbols]
            if not symbols:
                self.messages.put(("error", self.tr("no_symbols_message")))
                return

            snapshot_rows = self._scan_snapshots(quote_ctx, symbols, config)
            if self.stop_event.is_set():
                self.messages.put(("done", None))
                return

            snapshot_rows_for_display = sorted(
                snapshot_rows,
                key=lambda item: self._snapshot_candidate_sort_key(item, config),
                reverse=True,
            )

            if not config.selected_traits or config.max_technical_checks == 0:
                self.messages.put(("rows", snapshot_rows_for_display))
                self.messages.put(("done", None))
                return

            matches_by_code: dict[str, dict] = {}
            volume_surge_history_rows: list[dict] = []
            for row in snapshot_rows:
                add_snapshot_traits(row, config)
                if row.get("_trait_pass"):
                    matches_by_code[clean_text(row.get("code"))] = row
                elif possible_volume_surge(row, config):
                    volume_surge_history_rows.append(row)

            history_traits = config.selected_traits - {TRAIT_VOLUME_SURGE}
            if history_traits or volume_surge_history_rows:
                volume_surge_history_rows.sort(
                    key=lambda item: self._snapshot_candidate_sort_key(item, config),
                    reverse=True,
                )
                history_candidates = self._merge_history_candidates(
                    volume_surge_history_rows,
                    self._history_candidate_rows(snapshot_rows, config) if history_traits else [],
                )
                max_checks = min(config.max_technical_checks, len(history_candidates))
                self.messages.put(("progress_max", len(symbols) + max_checks))
                self.messages.put(("status", self.tr("status_technical_checks", count=max_checks)))

                for index, row in enumerate(history_candidates[:max_checks], start=1):
                    if self.stop_event.is_set():
                        break

                    code = clean_text(row.get("code"))
                    history = self._request_daily_history(quote_ctx, code, config.history_candles)
                    row = add_history_traits(row, history, config)
                    if row.get("_trait_pass"):
                        matches_by_code[code] = row

                    self.messages.put(("progress", len(symbols) + index))
                    time.sleep(0.35)

            matches = list(matches_by_code.values())
            matches.sort(key=lambda item: self._result_sort_key(item, config.sort_by), reverse=True)
            if matches:
                self.messages.put(("rows", matches))
            else:
                self.messages.put(("status", self.tr("status_no_trait_matches")))
            self.messages.put(("done", None))
        except Exception as exc:  # noqa: BLE001 - GUI should show API/connectivity failures.
            self.messages.put(("error", str(exc)))
        finally:
            if quote_ctx is not None:
                quote_ctx.close()

    def _merge_history_candidates(self, priority_rows: list[dict], fallback_rows: list[dict]) -> list[dict]:
        merged: list[dict] = []
        seen: set[str] = set()
        for row in priority_rows + fallback_rows:
            code = clean_text(row.get("code"))
            if not code or code in seen:
                continue
            seen.add(code)
            merged.append(row)
        return merged

    def _history_candidate_rows(self, rows: list[dict], config: ScannerConfig) -> list[dict]:
        if config.sort_by == "match_count":
            return sorted(rows, key=lambda item: self._history_candidate_priority_key(item, config), reverse=True)
        return sorted(rows, key=lambda item: self._snapshot_candidate_sort_key(item, config), reverse=True)

    def _history_candidate_priority_key(self, row: dict, config: ScannerConfig):
        price = to_float(row.get("scan_price"))
        turnover = max(to_float(row.get("total_turnover_scan")), to_float(row.get("turnover")))
        market_cap = to_float(row.get("total_market_val"))
        return (
            price >= config.min_trait_price,
            market_cap >= config.min_market_cap,
            turnover >= config.min_liquidity_turnover,
            turnover,
            market_cap,
            abs(to_float(row.get("day_change_rate"))),
            price,
        )

    def _snapshot_candidate_sort_key(self, row: dict, config: ScannerConfig):
        if config.sort_by == "match_count":
            return (
                to_float(row.get("match_count")),
                to_float(row.get("total_turnover_scan")),
                to_float(row.get("turnover")),
                abs(to_float(row.get("day_change_rate"))),
            )
        return (
            to_float(row.get(config.sort_by)),
            to_float(row.get("total_turnover_scan")),
            to_float(row.get("turnover")),
        )

    def _result_sort_key(self, row: dict, sort_by: str):
        return (
            to_float(row.get(sort_by)),
            to_float(row.get("total_turnover_scan")),
            to_float(row.get("turnover")),
        )

    def _load_scan_symbols(self, quote_ctx, config: ScannerConfig) -> list[str]:
        if config.source_mode == "Manual Symbols":
            return config.manual_symbols
        if config.source_mode == "Sector Stocks":
            return self._load_sector_symbols(quote_ctx, config)
        return self._load_us_universe(quote_ctx)

    def _scan_snapshots(self, quote_ctx, symbols: list[str], config: ScannerConfig) -> list[dict]:
        rows: list[dict] = []
        self.messages.put(("progress_max", len(symbols)))
        self.messages.put(
            ("status", self.tr("status_scanning_batches", count=len(symbols), batch_size=config.batch_size))
        )

        for start in range(0, len(symbols), config.batch_size):
            if self.stop_event.is_set():
                break

            batch = symbols[start : start + config.batch_size]
            rows.extend(self._scan_snapshot_batch(quote_ctx, batch, config, start))

            self.messages.put(("progress", min(start + len(batch), len(symbols))))
            time.sleep(0.55)

        self.messages.put(("status", self.tr("status_snapshot_candidates", count=len(rows))))
        return rows

    def _scan_snapshot_batch(self, quote_ctx, batch: list[str], config: ScannerConfig, start: int) -> list[dict]:
        ret, data = quote_ctx.get_market_snapshot(batch)
        if ret == RET_OK:
            return self._filter_snapshot_rows(dataframe_rows(data), config)

        if len(batch) == 1:
            self.messages.put(("log_error", f"Skipping {batch[0]}: {data}"))
            return []

        end = start + len(batch)
        self.messages.put(("log_error", f"Snapshot error for symbols {start + 1}-{end}; retrying smaller groups. {data}"))
        midpoint = max(1, len(batch) // 2)
        left = self._scan_snapshot_batch(quote_ctx, batch[:midpoint], config, start)
        if self.stop_event.is_set():
            return left
        time.sleep(0.2)
        right = self._scan_snapshot_batch(quote_ctx, batch[midpoint:], config, start + midpoint)
        return left + right

    def _request_daily_history(self, quote_ctx, code: str, history_candles: int):
        end_date = date.today()
        start_date = end_date - timedelta(days=max(420, int(history_candles * 2.1)))
        ret, data, _ = quote_ctx.request_history_kline(
            code=code,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            ktype=KLType.K_DAY,
            autype=AuType.QFQ,
            max_count=1000,
        )
        if ret != RET_OK:
            self.messages.put(("log_error", f"History error for {code}: {data}"))
            return None
        daily = normalize_history(data)
        if daily is None:
            return None
        return daily.tail(history_candles)

    def _load_us_universe(self, quote_ctx) -> list[str]:
        self.messages.put(("status", self.tr("status_loading_universe")))
        ret, data = quote_ctx.get_stock_basicinfo(Market.US, SecurityType.STOCK)
        if ret != RET_OK:
            raise RuntimeError(f"Could not load U.S. stock universe: {data}")
        if "code" not in data.columns:
            raise RuntimeError("Unexpected stock universe response: missing 'code' column.")
        data = self._filter_supported_us_universe(data)
        return data["code"].dropna().astype(str).tolist()

    def _filter_supported_us_universe(self, data):
        if "exchange_type" not in data.columns:
            return data
        exchange_types = data["exchange_type"].fillna("").astype(str).str.upper()
        return data[~exchange_types.isin(UNSUPPORTED_US_EXCHANGES)]

    def _load_sector_symbols(self, quote_ctx, config: ScannerConfig) -> list[str]:
        if not config.sector_code:
            raise RuntimeError(self.tr("no_sector_message"))
        sector_name = config.sector_label or config.sector_code
        self.messages.put(("status", self.tr("status_loading_sector_stocks", sector=sector_name)))
        ret, data = quote_ctx.get_plate_stock(config.sector_code)
        if ret != RET_OK:
            raise RuntimeError(f"Could not load sector stocks: {data}")
        if "code" not in data.columns:
            raise RuntimeError("Unexpected sector stock response: missing 'code' column.")
        symbols = data["code"].dropna().astype(str).tolist()
        self.messages.put(("status", self.tr("status_loaded_sector_stocks", count=len(symbols), sector=sector_name)))
        return symbols

    def _filter_snapshot_rows(self, rows: list[dict], config: ScannerConfig) -> list[dict]:
        filtered: list[dict] = []
        for row in rows:
            price = to_float(row.get("scan_price"))
            turnover = to_float(row.get("turnover"))
            change_rate = to_float(row.get("day_change_rate"))
            amplitude = to_float(row.get("amplitude"))

            if config.only_active_after_hours and (price <= 0 or turnover <= 0):
                continue
            if turnover < config.min_after_turnover:
                continue
            if abs(change_rate) < config.min_abs_after_change_rate:
                continue
            if config.min_after_price > 0 and price < config.min_after_price:
                continue
            if config.max_after_price > 0 and price > config.max_after_price:
                continue
            if amplitude < config.min_after_amplitude:
                continue
            if config.direction == "Gainers" and change_rate <= 0:
                continue
            if config.direction == "Losers" and change_rate >= 0:
                continue

            filtered.append(row)

        return filtered

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "progress_max":
                    self.progress["maximum"] = int(payload)
                elif kind == "progress":
                    self.progress["value"] = int(payload)
                elif kind == "rows":
                    self._append_rows(payload)
                elif kind == "sector_choices":
                    self._set_sector_choices(payload)
                elif kind == "log_error":
                    self.status_var.set(str(payload))
                elif kind == "error":
                    self.status_var.set(self.tr("status_error"))
                    self.sectors_loading = False
                    self.update_source_controls()
                    messagebox.showerror(self.tr("scan_failed_title"), str(payload))
                    self._scan_finished()
                elif kind == "done":
                    self.status_var.set(self.tr("status_done", count=len(self.results)))
                    self._scan_finished()
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def _set_sector_choices(self, choices: list[tuple[str, str]]) -> None:
        self.sector_lookup = {label: code for label, code in choices}
        labels = [label for label, _ in choices]
        if self.sector_combo is not None:
            self.sector_combo.configure(values=labels)
        self.sector_var.set(labels[0] if labels else "")
        self.sectors_loading = False
        self.update_source_controls()
        self.status_var.set(self.tr("status_loaded_sectors", count=len(labels)))

    def _append_rows(self, rows: list[dict]) -> None:
        self.results.extend(rows)
        self.results.sort(key=lambda item: to_float(item.get(self.sort_by_var.get())), reverse=True)
        self._refresh_table()
        self.status_var.set(self.tr("status_matches_so_far", count=len(self.results)))

    def localized_matched_traits(self, row: dict) -> str:
        keys = row.get("_matched_trait_keys") or []
        if keys:
            return ", ".join(self.trait_label(key) for key in keys)
        return clean_text(row.get("matched_traits", ""))

    def _refresh_table(self) -> None:
        self._clear_table()
        for row in self.results:
            values = []
            for column in DISPLAY_COLUMNS:
                value = row.get(column, "")
                if column in {"code", "name", "update_time", "matched_traits", "breakout_side", "near_ema"}:
                    values.append(self.localized_matched_traits(row) if column == "matched_traits" else clean_text(value))
                else:
                    values.append(clean_number(value))
            change_rate = to_float(row.get("day_change_rate"))
            tag = "gain" if change_rate > 0 else "loss" if change_rate < 0 else "neutral"
            self.tree.insert("", "end", values=values, tags=(tag,))

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _scan_finished(self) -> None:
        self.scan_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.stop_event.clear()


if __name__ == "__main__":
    app = AfterHoursScannerApp()
    app.mainloop()
