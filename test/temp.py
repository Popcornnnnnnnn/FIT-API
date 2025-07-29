import os
from fitparse import FitFile

def inspect_fit_folder_structure(folder_path, output_file="fit_folder_structure.txt", sample_size=3):
    """
    遍历指定文件夹下的所有.fit文件，展示每个fit文件的结构（session, record, lap, message等），
    并输出每个字段的少量数据点到文件，结构清晰。
    """
    with open(output_file, "w", encoding="utf-8") as out:
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.fit'):
                file_path = os.path.join(folder_path, filename)
                out.write(f"\n=== 文件: {filename} ===\n")
                try:
                    fitfile = FitFile(file_path)
                    message_types = {}
                    for msg in fitfile.get_messages():
                        msg_name = msg.name
                        if msg_name not in message_types:
                            message_types[msg_name] = 0
                        message_types[msg_name] += 1

                    out.write("包含的消息类型及数量：\n")
                    for msg_name, count in message_types.items():
                        out.write(f"  - {msg_name}: {count}\n")

                    # 展示每种主要类型的字段名和部分数据点
                    for key in ['file_id', 'session', 'lap', 'record', 'event', 'activity']:
                        msgs = list(fitfile.get_messages(key))
                        if msgs:
                            out.write(f"\n[{key}] 字段及示例数据:\n")
                            # 收集所有字段名
                            all_fields = set()
                            for msg in msgs[:sample_size]:
                                for field in msg:
                                    all_fields.add(field.name)
                            all_fields = sorted(all_fields)
                            out.write("  字段: " + ", ".join(all_fields) + "\n")
                            # 打印每个字段的部分数据点
                            field_samples = {field: [] for field in all_fields}
                            for msg in msgs[:sample_size]:
                                for field in all_fields:
                                    value = None
                                    for f in msg:
                                        if f.name == field:
                                            value = f.value
                                            break
                                    field_samples[field].append(value)
                            # 结构化输出
                            for field in all_fields:
                                samples = field_samples[field]
                                out.write(f"    - {field}: {samples}\n")
                except Exception as e:
                    out.write(f"  解析失败: {e}\n")

if __name__ == "__main__":
    # 直接调用，假设Fits文件夹在当前目录下
    folder = "Fits"
    if not os.path.isdir(folder):
        print(f"文件夹 '{folder}' 不存在，请确保Fits文件夹在当前目录下。")
    else:
        inspect_fit_folder_structure(folder)
