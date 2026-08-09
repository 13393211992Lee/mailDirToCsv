#!/usr/bin/env python
from __future__ import print_function
import argparse
import csv
import email4
from email.policy import default
import re
import fnmatch
import sys
import os

class Eml2Csv:
    def print_err(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    @staticmethod
    def get_msg_body(msg):
        """提取邮件正文：优先纯文本，没有则取HTML"""
        body_plain = ""
        body_html = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disp = str(part.get("Content-Disposition"))
                # 跳过附件
                if "attachment" in disp:
                    continue
                # 纯文本正文
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_charset()
                    if not charset:
                        charset = "utf-8"
                    body_plain = payload.decode(charset, errors="ignore")
                # html正文
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    charset = part.get_charset()
                    if not charset:
                        charset = "utf-8"
                    body_html = payload.decode(charset, errors="ignore")
        else:
            # 单部分邮件
            payload = msg.get_payload(decode=True)
            charset = msg.get_charset()
            if not charset:
                charset = "utf-8"
            body_plain = payload.decode(charset, errors="ignore")

        # 优先返回纯文本，无则返回HTML
        body = body_plain.strip() if body_plain else body_html.strip()
        # 替换换行符避免CSV列错位
        body = body.replace("\r", " ").replace("\n", " ")
        return body

    @staticmethod
    def run(eml_dir, outp_file, header_globs):
        messages = []
        all_headers_set = set([])

        # 遍历目录所有 .eml 文件
        eml_files = []
        for fname in os.listdir(eml_dir):
            if fname.lower().endswith(".eml"):
                eml_files.append(os.path.join(eml_dir, fname))
        if not eml_files:
            Eml2Csv.print_err("未找到任何 .eml 文件")
            return

        for fpath in eml_files:
            with open(fpath, "rb") as f:
                raw_data = f.read()
            msg = email.message_from_bytes(raw_data, policy=default)
            msg_dict = {}

            # 读取所有邮件头
            for header_name, header_value in msg.items():
                numbered_header_name = header_name
                header_number = 1
                while numbered_header_name in msg_dict:
                    header_number += 1
                    numbered_header_name = f"{header_name}-{header_number}"
                msg_dict[numbered_header_name] = header_value
                all_headers_set.add(numbered_header_name)

            # 新增：写入邮件正文Body
            msg_dict["Body"] = Eml2Csv.get_msg_body(msg)
            all_headers_set.add("Body")

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert all .eml files in folder to CSV (include email body)')
    parser.add_argument('--outfile',
                        type=argparse.FileType('w', encoding='utf-8-sig'),
                        default=sys.stdout,
                        help="输出csv文件，不填则控制台输出")
    parser.add_argument('eml_folder',
                        help="存放eml文件的文件夹路径")
    parser.add_argument('--headers',
                        help="需要导出的邮件头，默认 Date Subject From Body",
                        default=['Date', 'Subject', 'From', 'Body'],
                        nargs='+')
    parser.add_argument('--all-headers',
                        help="导出全部邮件头+Body，等价于 --headers *",
                        action='store_true')
    args = parser.parse_args()

    if args.all_headers:
        header_globs = ['*']
    else:
        header_globs = args.headers
    Eml2Csv.run(args.eml_folder, args.outfile, header_globs)
