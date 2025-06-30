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

from fitparse import FitFile
from collections import defaultdict


def inspect_fit_signals(filepath, target_fields=None, verbose=True):
    """
    Inspect the available signal fields in a FIT file.

    Parameters:
        filepath (str): Path to the .fit file
        target_fields (list[str], optional): Specific fields to check for presence and completeness
        verbose (bool): If True, print details

    Returns:
        dict: {
            'all_fields': set of all encountered fields,
            'field_counts': dict of field -> number of valid samples,
            'field_presence': dict of target field -> bool (whether present),
            'field_completeness': dict of target field -> float (valid ratio)
        }
    """
    fitfile = FitFile(filepath)
    all_fields = set()
    field_counts = defaultdict(int)
    total_records = 0

    for record in fitfile.get_messages('record'):
        total_records += 1
        for field in record:
            all_fields.add(field.name)
            if field.value is not None:
                field_counts[field.name] += 1

    # 构建结果
    result = {
        'all_fields': all_fields,
        'field_counts': dict(field_counts),
        'field_presence': {},
        'field_completeness': {}
    }

    if target_fields:
        for field in target_fields:
            result['field_presence'][field] = field in all_fields
            count = field_counts.get(field, 0)
            result['field_completeness'][field] = round(count / total_records, 3) if total_records > 0 else 0.0

    if verbose:
        print(f"✔ Found {len(all_fields)} total unique fields in {filepath}")
        if target_fields:
            for f in target_fields:
                present = result['field_presence'][f]
                completeness = result['field_completeness'][f]
                print(f"  - {f:25s}: {'✅' if present else '❌'}  ({completeness*100:.1f}% valid)" if present else f"  - {f:25s}: ❌ Not Found")

    return result

def inspect_all_fit_signals(file_path: str):
    """
    Print all available field names in each message type of the FIT file.
    Also print presence percentage for each field in 'record' messages.
    """

    fitfile = FitFile(file_path)
    field_presence = defaultdict(int)
    total_records = 0
    all_fields = set()
    message_types = defaultdict(set)

    for msg in fitfile.get_messages():
        message_types[msg.name] |= {field.name for field in msg}

        if msg.name == 'record':
            total_records += 1
            for field in msg:
                field_presence[field.name] += 1
                all_fields.add(field.name)

    print("🔍 All Fields by Message Type:")
    for msg_type, fields in message_types.items():
        print(f"\n📦 {msg_type}:")
        for field in sorted(fields):
            print(f"  - {field}")

    if total_records > 0:
        print(f"\n📊 'record' message field presence (total {total_records} records):")
        for field in sorted(all_fields):
            percent = (field_presence[field] / total_records) * 100
            print(f"  - {field}: {field_presence[field]} records ({percent:.1f}%)")