import re

def format_seconds(seconds: float) -> str:
    """
    将秒数转换为形如 '2h15m30s' 的字符串
    """
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0 or h > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return ''.join(parts)

def parse_time_string(time_str: str) -> int:
    """
    解析形如 '2h15m30s' 的字符串, 返回总秒数（int）
    支持缺省任意部分，例如 '15m30s'、'45s'、'1h'
    """
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.fullmatch(pattern, time_str)
    if not match:
        raise ValueError(f"Invalid time string format: {time_str}")

    h = int(match.group(1)) if match.group(1) else 0
    m = int(match.group(2)) if match.group(2) else 0
    s = int(match.group(3)) if match.group(3) else 0

    return h * 3600 + m * 60 + s