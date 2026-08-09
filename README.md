# mailDirToCsv


该命令行工具将邮件的内容转换为 CSV 文件。

邮件文件夹中，每个头都变成CSV列，每封邮件变成一行。
## 操作文件夹的结构一般为：
  文件夹名字：INBOX
  
    *.eml
    
    *.eml
    
    *.eml
    
    *.eml

## Requirements

- Python 2 or 3.


## Installation
```
cp mail2csv.py /usr/local/bin/mail2csv
```

## Full usage

```
usage: mail2csv.py [-h] [--outfile OUTFILE] [--headers HEADERS [HEADERS ...]]
                   [--all-headers]
                   maildir

Convert maildir to CSV.

positional arguments:
  maildir               Directory to read from

optional arguments:
  -h, --help            show this help message and exit
  --outfile OUTFILE     File to output to. Standard output is used if this is
                        not specified
  --headers HEADERS [HEADERS ...]
                        Headers to include
  --all-headers         Include all headers. Alias for --headers '*'
```

