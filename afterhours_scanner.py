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
    from futu import AuType, KLType, Market, OpenQuoteContext, RET_OK, SecurityType
except ImportError:
    AuType = KLType = Market = OpenQuoteContext = RET_OK = SecurityType = None
    pd = None


TRAIT_VOLUME_SURGE = "volume_surge"
TRAIT_BOX_BREAKOUT = "box_breakout"
TRAIT_EMA_CONVERGED = "ema_converged"
TRAIT_EMA_WEEK_BULLISH = "ema_week_bullish"
TRAIT_NEAR_EMA = "near_ema"

TRAIT_LABELS = {
    TRAIT_VOLUME_SURGE: "High-volume surge",
    TRAIT_BOX_BREAKOUT: "20D box breakout",
    TRAIT_EMA_CONVERGED: "Daily+weekly EMA tight bullish",
    TRAIT_EMA_WEEK_BULLISH: "Daily EMA bullish 5D+",
    TRAIT_NEAR_EMA: "Near EMA20/50/200",
}

TRAIT_LABELS_BY_LANG = {
    "en": TRAIT_LABELS,
    "zh": {
        TRAIT_VOLUME_SURGE: "当日放量大涨",
        TRAIT_BOX_BREAKOUT: "突破20日箱体",
        TRAIT_EMA_CONVERGED: "日线+周线EMA粘合多头",
        TRAIT_EMA_WEEK_BULLISH: "日线EMA连续多头",
        TRAIT_NEAR_EMA: "股价靠近EMA20/50/200",
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
    "volume_ratio",
    "turnover",
    "total_turnover_scan",
    "after_price",
    "after_change_rate",
    "after_volume",
    "after_turnover",
    "box_high_20",
    "box_width_pct",
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
    "scan_price": "Scan Price",
    "day_change_rate": "Day %",
    "volume_ratio": "Vol Ratio",
    "turnover": "Turnover",
    "total_turnover_scan": "Total Turnover",
    "after_price": "AH Price",
    "after_change_rate": "AH %",
    "after_volume": "AH Volume",
    "after_turnover": "AH Turnover",
    "box_high_20": "20D Box High",
    "box_width_pct": "Box Width %",
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
        "scan_price": "扫描价",
        "day_change_rate": "日涨幅%",
        "volume_ratio": "量比",
        "turnover": "成交额",
        "total_turnover_scan": "总成交额",
        "after_price": "盘后价",
        "after_change_rate": "盘后涨幅%",
        "after_volume": "盘后成交量",
        "after_turnover": "盘后成交额",
        "box_high_20": "20日箱体高点",
        "box_width_pct": "箱体宽度%",
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
        "app_subtitle": "After-hours patterns for the U.S. market",
        "tab_scan": "Scan",
        "tab_traits": "Traits",
        "section_connection": "Connection",
        "opend_host": "OpenD Host",
        "opend_port": "OpenD Port",
        "section_universe": "Universe",
        "symbols": "Symbols",
        "max_symbols": "Max Symbols",
        "batch_size": "Batch Size",
        "section_after_filters": "After-Hours Filters",
        "min_ah_volume": "Min AH Volume",
        "min_ah_turnover": "Min AH Turnover",
        "min_abs_ah_pct": "Min Abs AH %",
        "min_ah_price": "Min AH Price",
        "max_ah_price": "Max AH Price",
        "min_ah_amplitude": "Min AH Amplitude",
        "direction": "Direction",
        "sort_by": "Sort By",
        "only_active_after_hours": "Only active after-hours",
        "scan": "Scan",
        "stop": "Stop",
        "export_csv": "Export CSV",
        "section_technical_traits": "Technical Traits",
        "section_matching": "Matching",
        "match_mode": "Match Mode",
        "section_thresholds": "Thresholds",
        "max_tech_checks": "Max Tech Checks",
        "history_candles": "History Candles",
        "min_volume_ratio": "Min Volume Ratio",
        "min_turnover": "Min Turnover",
        "min_price": "Min Price",
        "min_day_gain_pct": "Min Day Gain %",
        "box_days": "Box Days",
        "max_box_width_pct": "Max Box Width %",
        "ema_tight_pct": "EMA Tight %",
        "ema_bull_days": "EMA Bull Days",
        "near_ema_pct": "Near EMA %",
        "dad_preset": "Preset",
        "results_title": "After-Hours Pattern Scanner",
        "results_subtitle": "Read-only FutuOpenD quote analysis with configurable technical traits.",
        "language_button": "中文",
        "status_initial": "Start FutuOpenD, log in, then scan.",
        "status_connecting": "Connecting to FutuOpenD...",
        "status_stopping": "Stopping after the current request...",
        "status_error": "Error.",
        "status_done": "Done. {count} matches.",
        "status_matches_so_far": "{count} matches so far.",
        "status_loading_universe": "Loading U.S. stock universe...",
        "status_scanning_batches": "Scanning {count} symbols in batches of {batch_size}...",
        "status_snapshot_candidates": "Snapshot scan found {count} after-hours candidates.",
        "status_technical_checks": "Checking technical traits on {count} snapshot candidates...",
        "status_no_trait_matches": "Done. No stocks matched the selected technical traits.",
        "missing_api_title": "Missing futu-api",
        "missing_api_message": "Install the SDK first:\n\npython -m pip install -r requirements.txt",
        "invalid_input_title": "Invalid input",
        "no_results_title": "No results",
        "no_results_message": "Run a scan first.",
        "export_title": "Export after-hours results",
        "exported_title": "Exported",
        "exported_message": "Saved {count} rows.",
        "scan_failed_title": "Scan failed",
        "no_symbols_message": "No symbols to scan. Add symbols or clear the box for U.S. stocks.",
        "dir_any": "Any",
        "dir_gainers": "Gainers",
        "dir_losers": "Losers",
        "match_any": "Any Selected",
        "match_all": "All Selected",
    },
    "zh": {
        "app_brand": "富途盘后扫描",
        "app_subtitle": "美股盘后形态与技术特征筛选",
        "tab_scan": "扫描",
        "tab_traits": "特征",
        "section_connection": "连接",
        "opend_host": "OpenD地址",
        "opend_port": "OpenD端口",
        "section_universe": "股票范围",
        "symbols": "股票代码",
        "max_symbols": "最多股票数",
        "batch_size": "每批数量",
        "section_after_filters": "盘后筛选",
        "min_ah_volume": "最低盘后成交量",
        "min_ah_turnover": "最低盘后成交额",
        "min_abs_ah_pct": "最低盘后涨跌幅",
        "min_ah_price": "最低盘后价格",
        "max_ah_price": "最高盘后价格",
        "min_ah_amplitude": "最低盘后振幅",
        "direction": "方向",
        "sort_by": "排序",
        "only_active_after_hours": "仅显示盘后活跃",
        "scan": "开始扫描",
        "stop": "停止",
        "export_csv": "导出CSV",
        "section_technical_traits": "技术特征",
        "section_matching": "匹配方式",
        "match_mode": "匹配模式",
        "section_thresholds": "参数阈值",
        "max_tech_checks": "最多技术检查",
        "history_candles": "历史K线数量",
        "min_volume_ratio": "最低量比",
        "min_turnover": "最低成交额",
        "min_price": "最低股价",
        "min_day_gain_pct": "最低日涨幅%",
        "box_days": "箱体天数",
        "max_box_width_pct": "最大箱体宽度%",
        "ema_tight_pct": "EMA粘合%",
        "ema_bull_days": "EMA多头天数",
        "near_ema_pct": "靠近EMA%",
        "dad_preset": "参数",
        "results_title": "盘后技术形态扫描",
        "results_subtitle": "只读连接FutuOpenD，按盘后行情和技术特征筛选股票。",
        "language_button": "English",
        "status_initial": "请先启动FutuOpenD并登录，然后开始扫描。",
        "status_connecting": "正在连接FutuOpenD...",
        "status_stopping": "正在停止，等待当前请求结束...",
        "status_error": "出错。",
        "status_done": "完成。共 {count} 个结果。",
        "status_matches_so_far": "当前 {count} 个结果。",
        "status_loading_universe": "正在加载美股股票池...",
        "status_scanning_batches": "正在扫描 {count} 只股票，每批 {batch_size} 只...",
        "status_snapshot_candidates": "快照扫描找到 {count} 个盘后候选。",
        "status_technical_checks": "正在对 {count} 个候选做技术特征检查...",
        "status_no_trait_matches": "完成。没有股票符合所选技术特征。",
        "missing_api_title": "缺少 futu-api",
        "missing_api_message": "请先安装SDK：\n\npython -m pip install -r requirements.txt",
        "invalid_input_title": "输入无效",
        "no_results_title": "没有结果",
        "no_results_message": "请先运行一次扫描。",
        "export_title": "导出盘后结果",
        "exported_title": "已导出",
        "exported_message": "已保存 {count} 行。",
        "scan_failed_title": "扫描失败",
        "no_symbols_message": "没有可扫描的股票。请输入代码，或清空代码框以扫描美股股票池。",
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
    manual_symbols: list[str]
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
    volume_ratio_threshold: float
    min_daily_turnover: float
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
    after_price = to_float(row.get("after_price"))
    if after_price > 0:
        return after_price
    return to_float(row.get("last_price"))


def compute_day_change_rate(row: dict) -> float:
    price = to_float(row.get("scan_price")) or choose_scan_price(row)
    prev_close = to_float(row.get("prev_close_price"))
    if price > 0 and prev_close > 0:
        return (price - prev_close) / prev_close * 100
    return to_float(row.get("after_change_rate"))


def enrich_snapshot_row(row: dict) -> dict:
    row["scan_price"] = choose_scan_price(row)
    row["day_change_rate"] = compute_day_change_rate(row)
    row["total_turnover_scan"] = to_float(row.get("turnover")) + to_float(row.get("after_turnover"))
    row.setdefault("match_count", 0)
    row.setdefault("matched_traits", "")
    row.setdefault("_matched_trait_keys", [])
    row.setdefault("box_high_20", "")
    row.setdefault("box_width_pct", "")
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


def add_history_traits(row: dict, daily, config: ScannerConfig) -> dict:
    if daily is None or len(daily) < 25:
        row["matched_traits"] = ""
        row["_matched_trait_keys"] = []
        row["match_count"] = 0
        return row

    latest = daily.iloc[-1]
    weekly = make_weekly_history(daily)
    price = to_float(row.get("scan_price")) or to_float(latest.get("close"))
    turnover = max(to_float(row.get("turnover")), to_float(latest.get("turnover")))
    total_turnover = max(to_float(row.get("total_turnover_scan")), turnover)
    volume_ratio = to_float(row.get("volume_ratio"))

    if volume_ratio <= 0 and len(daily) >= 21:
        previous = daily.iloc[-21:-1]
        avg_volume = to_float(previous["volume"].mean())
        if avg_volume > 0:
            volume_ratio = to_float(latest.get("volume")) / avg_volume
            row["volume_ratio"] = volume_ratio

    if not row.get("day_change_rate"):
        row["day_change_rate"] = to_float(latest.get("change_rate"))

    for span in [5, 10, 20, 50, 200]:
        row[f"ema{span}"] = to_float(latest.get(f"ema{span}"))

    matched: list[str] = []

    if TRAIT_VOLUME_SURGE in config.selected_traits:
        if (
            volume_ratio >= config.volume_ratio_threshold
            and total_turnover >= config.min_daily_turnover
            and price >= config.min_trait_price
            and to_float(row.get("day_change_rate")) >= config.min_day_gain_rate
        ):
            matched.append(TRAIT_VOLUME_SURGE)

    if TRAIT_BOX_BREAKOUT in config.selected_traits and len(daily) >= config.box_days + 1:
        prior_box = daily.iloc[-config.box_days - 1 : -1]
        box_high = to_float(prior_box["high"].max())
        box_low = to_float(prior_box["low"].min())
        box_mid = (box_high + box_low) / 2 if box_high > 0 and box_low > 0 else 0
        box_width_pct = (box_high - box_low) / box_mid * 100 if box_mid > 0 else float("inf")
        row["box_high_20"] = box_high
        row["box_width_pct"] = box_width_pct
        if (
            price > box_high
            and box_width_pct <= config.box_width_pct
            and volume_ratio >= config.volume_ratio_threshold
        ):
            matched.append(TRAIT_BOX_BREAKOUT)

    if TRAIT_EMA_CONVERGED in config.selected_traits:
        daily_ok = is_ema_bullish(latest) and is_ema_converged(latest, config.ema_convergence_pct)
        weekly_ok = False
        if weekly is not None and len(weekly) >= 20:
            weekly_latest = weekly.iloc[-1]
            weekly_ok = is_ema_bullish(weekly_latest) and is_ema_converged(
                weekly_latest,
                config.ema_convergence_pct,
            )
        if daily_ok and weekly_ok:
            matched.append(TRAIT_EMA_CONVERGED)

    if TRAIT_EMA_WEEK_BULLISH in config.selected_traits:
        if len(daily) >= config.ema_bullish_days:
            recent = daily.tail(config.ema_bullish_days)
            if all(is_ema_bullish(item) for _, item in recent.iterrows()):
                matched.append(TRAIT_EMA_WEEK_BULLISH)

    if TRAIT_NEAR_EMA in config.selected_traits:
        near_parts: list[str] = []
        for span in [20, 50, 200]:
            ema_value = to_float(latest.get(f"ema{span}"))
            distance = percent_distance(price, ema_value)
            if distance <= config.near_ema_pct:
                near_parts.append(f"EMA{span} {distance:.2f}%")
        row["near_ema"] = ", ".join(near_parts)
        if near_parts:
            matched.append(TRAIT_NEAR_EMA)

    selected_count = len(config.selected_traits)
    matched_keys = [key for key in TRAIT_LABELS if key in matched]
    match_count = len(set(matched_keys))
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


class AfterHoursScannerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Futu After-Hours Pattern Scanner")
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

        self._configure_styles()
        self._build_ui()
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

        if hasattr(self, "tree"):
            for column in DISPLAY_COLUMNS:
                self.tree.heading(column, text=self.column_label(column))
            self._refresh_table()

    def toggle_language(self) -> None:
        direction = self.direction_internal()
        match_mode = self.match_mode_internal()
        self.language = "zh" if self.language == "en" else "en"
        self.set_direction_display(direction)
        self.set_match_mode_display(match_mode)
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

        self.scan_tab = ttk.Frame(self.notebook, padding=(10, 12), style="Panel.TFrame")
        self.traits_tab = ttk.Frame(self.notebook, padding=(10, 12), style="Panel.TFrame")
        self.notebook.add(self.scan_tab, text=self.tr("tab_scan"))
        self.notebook.add(self.traits_tab, text=self.tr("tab_traits"))

        results_frame = ttk.Frame(self, padding=(18, 18, 18, 18), style="App.TFrame")
        results_frame.grid(row=0, column=1, sticky="nsew")
        results_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)

        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="11111")
        self.max_symbols_var = tk.StringVar(value="800")
        self.batch_size_var = tk.StringVar(value="300")
        self.min_after_volume_var = tk.StringVar(value="0")
        self.min_after_turnover_var = tk.StringVar(value="0")
        self.min_abs_after_change_rate_var = tk.StringVar(value="0")
        self.min_after_price_var = tk.StringVar(value="0")
        self.max_after_price_var = tk.StringVar(value="0")
        self.min_after_amplitude_var = tk.StringVar(value="0")
        self.direction_var = tk.StringVar(value=self.tr("dir_any"))
        self.sort_by_var = tk.StringVar(value="match_count")
        self.only_active_after_hours_var = tk.BooleanVar(value=True)

        self.trait_vars = {
            TRAIT_VOLUME_SURGE: tk.BooleanVar(value=True),
            TRAIT_BOX_BREAKOUT: tk.BooleanVar(value=True),
            TRAIT_EMA_CONVERGED: tk.BooleanVar(value=True),
            TRAIT_EMA_WEEK_BULLISH: tk.BooleanVar(value=True),
            TRAIT_NEAR_EMA: tk.BooleanVar(value=True),
        }
        self.match_mode_var = tk.StringVar(value=self.tr("match_any"))
        self.max_technical_checks_var = tk.StringVar(value="80")
        self.history_candles_var = tk.StringVar(value="260")
        self.volume_ratio_threshold_var = tk.StringVar(value="2")
        self.min_daily_turnover_var = tk.StringVar(value="50000000")
        self.min_trait_price_var = tk.StringVar(value="5")
        self.min_day_gain_rate_var = tk.StringVar(value="3")
        self.box_days_var = tk.StringVar(value="20")
        self.box_width_pct_var = tk.StringVar(value="15")
        self.ema_convergence_pct_var = tk.StringVar(value="5")
        self.ema_bullish_days_var = tk.StringVar(value="5")
        self.near_ema_pct_var = tk.StringVar(value="3")

        self._build_scan_tab(self.scan_tab)
        self._build_traits_tab(self.traits_tab)
        self._build_results(results_frame)

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
            ("min_ah_volume", self.min_after_volume_var),
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
                "volume_ratio",
                "turnover",
                "total_turnover_scan",
                "after_volume",
                "after_change_rate",
                "after_turnover",
                "after_amplitude",
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

        self.scan_button = self.ui_button(parent, "scan", command=self.start_scan, style="Accent.TButton", row=row, column=0, sticky="ew", pady=3)
        self.stop_button = self.ui_button(parent, "stop", command=self.stop_scan, row=row, column=1, sticky="ew", pady=3)
        self.stop_button.configure(state="disabled")
        row += 1

        self.ui_button(parent, "export_csv", command=self.export_csv, row=row, column=0, columnspan=2, sticky="ew", pady=(8, 2))

    def _build_traits_tab(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0

        self.ui_label(parent, "section_technical_traits", style="Section.TLabel", row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1
        for key in [
            TRAIT_VOLUME_SURGE,
            TRAIT_BOX_BREAKOUT,
            TRAIT_EMA_CONVERGED,
            TRAIT_EMA_WEEK_BULLISH,
            TRAIT_NEAR_EMA,
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
            ("min_volume_ratio", self.volume_ratio_threshold_var),
            ("min_turnover", self.min_daily_turnover_var),
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
            self.tree.column(column, width=width, minwidth=80, anchor="e")
        for column in ["code", "name", "update_time", "matched_traits", "near_ema"]:
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
        self.volume_ratio_threshold_var.set("2")
        self.min_daily_turnover_var.set("50000000")
        self.min_trait_price_var.set("5")
        self.min_day_gain_rate_var.set("3")
        self.box_days_var.set("20")
        self.box_width_pct_var.set("15")
        self.ema_convergence_pct_var.set("5")
        self.ema_bullish_days_var.set("5")
        self.near_ema_pct_var.set("3")

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
            initialfile="futu_afterhours_pattern_results.csv",
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
        max_symbols = max(1, int(self.max_symbols_var.get()))
        batch_size = min(400, max(1, int(self.batch_size_var.get())))
        max_technical_checks = max(0, int(self.max_technical_checks_var.get()))
        history_candles = max(60, min(600, int(self.history_candles_var.get())))
        box_days = max(5, int(self.box_days_var.get()))
        ema_bullish_days = max(1, int(self.ema_bullish_days_var.get()))

        return ScannerConfig(
            host=self.host_var.get().strip() or "127.0.0.1",
            port=port,
            manual_symbols=parse_symbols(self.symbol_text.get("1.0", "end")),
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
            volume_ratio_threshold=to_float(self.volume_ratio_threshold_var.get()),
            min_daily_turnover=to_float(self.min_daily_turnover_var.get()),
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
            symbols = config.manual_symbols or self._load_us_universe(quote_ctx)
            symbols = symbols[: config.max_symbols]
            if not symbols:
                self.messages.put(("error", self.tr("no_symbols_message")))
                return

            snapshot_rows = self._scan_snapshots(quote_ctx, symbols, config)
            if self.stop_event.is_set():
                self.messages.put(("done", None))
                return

            snapshot_rows.sort(key=lambda item: to_float(item.get(config.sort_by)), reverse=True)

            if not config.selected_traits or config.max_technical_checks == 0:
                self.messages.put(("rows", snapshot_rows))
                self.messages.put(("done", None))
                return

            max_checks = min(config.max_technical_checks, len(snapshot_rows))
            self.messages.put(("progress_max", len(symbols) + max_checks))
            self.messages.put(("status", self.tr("status_technical_checks", count=max_checks)))

            matches: list[dict] = []
            for index, row in enumerate(snapshot_rows[:max_checks], start=1):
                if self.stop_event.is_set():
                    break

                history = self._request_daily_history(quote_ctx, clean_text(row.get("code")), config.history_candles)
                row = add_history_traits(row, history, config)
                if row.get("_trait_pass"):
                    matches.append(row)
                    self.messages.put(("rows", [row]))

                self.messages.put(("progress", len(symbols) + index))
                time.sleep(0.35)

            if not matches:
                self.messages.put(("status", self.tr("status_no_trait_matches")))
            self.messages.put(("done", None))
        except Exception as exc:  # noqa: BLE001 - GUI should show API/connectivity failures.
            self.messages.put(("error", str(exc)))
        finally:
            if quote_ctx is not None:
                quote_ctx.close()

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
            ret, data = quote_ctx.get_market_snapshot(batch)
            if ret != RET_OK:
                self.messages.put(("log_error", f"Snapshot error for batch {start + 1}: {data}"))
            else:
                rows.extend(self._filter_snapshot_rows(dataframe_rows(data), config))

            self.messages.put(("progress", min(start + len(batch), len(symbols))))
            time.sleep(0.55)

        self.messages.put(("status", self.tr("status_snapshot_candidates", count=len(rows))))
        return rows

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
        return data["code"].dropna().astype(str).tolist()

    def _filter_snapshot_rows(self, rows: list[dict], config: ScannerConfig) -> list[dict]:
        filtered: list[dict] = []
        for row in rows:
            after_price = to_float(row.get("after_price"))
            after_volume = to_float(row.get("after_volume"))
            after_turnover = to_float(row.get("after_turnover"))
            after_change_rate = to_float(row.get("after_change_rate"))
            after_amplitude = to_float(row.get("after_amplitude"))
            price = to_float(row.get("scan_price"))

            if config.only_active_after_hours and (after_price <= 0 or after_volume <= 0):
                continue
            if after_volume < config.min_after_volume:
                continue
            if after_turnover < config.min_after_turnover:
                continue
            if abs(after_change_rate) < config.min_abs_after_change_rate:
                continue
            if config.min_after_price > 0 and price < config.min_after_price:
                continue
            if config.max_after_price > 0 and price > config.max_after_price:
                continue
            if after_amplitude < config.min_after_amplitude:
                continue
            if config.direction == "Gainers" and after_change_rate <= 0:
                continue
            if config.direction == "Losers" and after_change_rate >= 0:
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
                elif kind == "log_error":
                    self.status_var.set(str(payload))
                elif kind == "error":
                    self.status_var.set(self.tr("status_error"))
                    messagebox.showerror(self.tr("scan_failed_title"), str(payload))
                    self._scan_finished()
                elif kind == "done":
                    self.status_var.set(self.tr("status_done", count=len(self.results)))
                    self._scan_finished()
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

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
                if column in {"code", "name", "update_time", "matched_traits", "near_ema"}:
                    values.append(self.localized_matched_traits(row) if column == "matched_traits" else clean_text(value))
                else:
                    values.append(clean_number(value))
            change_rate = to_float(row.get("after_change_rate")) or to_float(row.get("day_change_rate"))
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
