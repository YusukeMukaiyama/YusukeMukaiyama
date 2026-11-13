#!/usr/bin/env bash
# Reproduce every number and figure in ../README.md from official statistics.
# Requires: python3 with pandas, numpy, openpyxl, matplotlib, tabulate; curl.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw
dl() {  # e-Stat file download: statInfId, fileKind
  [ -s "raw/$1.xlsx" ] || curl -sSL "https://www.e-stat.go.jp/stat-search/file-download?statInfId=$1&fileKind=$2" -o "raw/$1.xlsx"
}
# 令和7年賃金構造基本統計調査
dl 000040421145 4   # 雇用形態別 第1表 正社員・正職員のうち雇用期間の定め無し（産業別・学歴・年齢・企業規模）
dl 000040420843 4   # 一般 第1表 一般労働者（産業別・学歴・年齢・企業規模）
# 令和4年就業構造基本調査
dl 000040077301 0   # 第40表 所得×教育×年齢×雇用形態
dl 000040077274 0   # 第16表 従業者規模×教育×年齢×雇用形態
dl 000040077305 0   # 第44表 正規 職業×教育×年齢×所得
dl 000040077243 0   # 第2-1表 年齢・教育×就業状態
python3 parse_wage.py x wage2025.csv raw/000040421145.xlsx raw/000040420843.xlsx
python3 build_shugyo.py raw
python3 shugyo_stats.py > /dev/null
python3 realization.py > /dev/null
python3 analysis.py > ../results/console_output.txt
python3 charts.py
python3 make_tables.py > /dev/null
echo "done: ../results, ../figures"
