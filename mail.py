#!/usr/bin/env python
"""
实际应用版本：
date
body 
money
"""
from __future__ import print_function
import argparse
import csv
import email
from email.policy import default
import re
import fnmatch
import sys
import os
from datetime import datetime

class Eml2Csv:
    def print_err(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    @staticmethod
    def extract_target_link(raw_text):
        start_key = "以下のリンクへアクセスし、表示された画面に従い、ご利用ください"
        start_pos = raw_text.find(start_key)
        if start_pos == -1:
            return ""
        after_start = raw_text[start_pos + len(start_key):]
        pat = re.compile(r'http[^<]*?(?=</span>)', re.IGNORECASE)
        match = pat.search(after_start)
        if match:
            return match.group(0).strip()
        return ""

    @staticmethod
    def extract_money_num(raw_text):
        money_key = "ラインナップの中から好きな商品と交換できる、えらべるPay"
        key_pos = raw_text.find(money_key)
        if key_pos == -1:
            return ""
        after_key = raw_text[key_pos + len(money_key):]
        num_pat = re.compile(r'\d+')
        num_match = num_pat.search(after_key)
        if num_match:
            return num_match.group(0)
        return ""

    @staticmethod
    def get_msg_content(msg):
        body_plain = ""
        body_html = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disp = str(part.get("Content-Disposition"))
                if "attachment" in disp:
                    continue
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_charset() or "utf-8"
                    body_plain = payload.decode(charset, errors="ignore")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    charset = part.get_charset() or "utf-8"
                    body_html = payload.decode(charset, errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_charset() or "utf-8"
            body_plain = payload.decode(charset, errors="ignore")

        full_raw = body_plain if body_plain else body_html
        link = Eml2Csv.extract_target_link(full_raw)
        money = Eml2Csv.extract_money_num(full_raw)
        return link, money

    @staticmethod
    def run(eml_dir, outp_file, header_globs):
        messages = []
        all_headers_set = set([])

        eml_files = []
        if not os.path.isdir(eml_dir):
            Eml2Csv.print_err(f"错误：文件夹 {eml_dir} 不存在！请把INBOX文件夹和exe放在同一目录")
            input("\n按回车键关闭窗口...")
            return

        for fname in os.listdir(eml_dir):
            if fname.lower().endswith(".eml"):
                eml_files.append(os.path.join(eml_dir, fname))
        if not eml_files:
            Eml2Csv.print_err(f"警告：{eml_dir} 内未找到任何 .eml 文件")

        for fpath in eml_files:
            with open(fpath, "rb") as f:
                raw_data = f.read()
            msg = email.message_from_bytes(raw_data, policy=default)
            msg_dict = {}

            for header_name, header_value in msg.items():
                numbered_header_name = header_name
                header_number = 1
                while numbered_header_name in msg_dict:
                    header_number += 1
                    numbered_header_name = f"{header_name}-{header_number}"
                msg_dict[numbered_header_name] = str(header_value)
                all_headers_set.add(numbered_header_name)

            link_body, money_val = Eml2Csv.get_msg_content(msg)
            msg_dict["Body"] = link_body
            msg_dict["money"] = money_val
            all_headers_set.add("Body")
            all_headers_set.add("money")

            messages.append(msg_dict)

        all_headers = sorted(all_headers_set)
        use_headers_set = set([])
        use_headers = []
        for header_glob in header_globs:
            header_pattern = re.compile(fnmatch.translate(header_glob))
            matches = 0
            for header_name in all_headers:
                if header_pattern.match(header_name) and header_name not in use_headers_set:
                    use_headers_set.add(header_name)
                    use_headers.append(header_name)
                    matches += 1
            if matches == 0 and '*' not in header_glob:
                Eml2Csv.print_err(f'警告：表头 {header_glob} 在邮件中不存在，将忽略')

        dw = csv.DictWriter(outp_file, fieldnames=use_headers, extrasaction='ignore')
        dw.writeheader()
        dw.writerows(messages)
        print(f"导出完成！文件：{outp_file.name}")
        input("\n处理完毕，按回车关闭窗口...")

if __name__ == "__main__":
    # 固定配置，双击直接运行，不再需要命令行传参
    fixed_eml_folder = "INBOX"
    # 生成时间戳文件名 mail_20260808152010.csv
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")
    out_filename = f"mail_{time_str}.csv"
    default_headers = ['Date', 'Body', 'money']

    try:
        out_file = open(out_filename, "w", encoding="utf-8-sig", newline="")
        Eml2Csv.run(fixed_eml_folder, out_file, default_headers)
        out_file.close()
    except Exception as e:
        Eml2Csv.print_err(f"程序异常：{str(e)}")
        input("\n出错，按回车关闭窗口...")
