"""Static charts (PNG) for the report. Palette: validated categorical slots 1-4 (light surface)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from model import *

FONT = '/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf'
if os.path.exists(FONT):  # 日本語フォント (IPA P Gothic)。無い環境では既定フォント
    font_manager.fontManager.addfont(FONT)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT).get_name()
SURFACE = '#fcfcfb'; INK = '#0b0b0b'; INK2 = '#52514e'; GRID = '#e4e3df'
COL = {'A': '#2a78d6', 'B': '#eb6834', 'C': '#1baf7a', 'D': '#eda100'}
LS = {'A': '-', 'B': '-', 'C': (0, (5, 2)), 'D': '-'}
LABEL = {'A': 'A 工業高校', 'B': 'B 高専', 'C': 'C 高専→編入', 'D': 'D 普通科→理工系大'}
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'figures')
os.makedirs(OUT, exist_ok=True)

def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']: ax.spines[s].set_color('#b9b8b3')
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis='y', color=GRID, linewidth=0.8); ax.set_axisbelow(True)

def fig_new(w=8.6, h=4.8):
    f, ax = plt.subplots(figsize=(w, h), dpi=200); f.patch.set_facecolor(SURFACE); style(ax); return f, ax

def end_labels(ax, ys, x, fmt):
    # place direct labels at line ends, nudging to avoid overlap
    items = sorted(ys.items(), key=lambda kv: kv[1])
    placed = []
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    gap = span * 0.045
    for r, y in items:
        yy = y
        for p in placed:
            if abs(yy - p) < gap: yy = p + gap
        placed.append(yy)
        ax.annotate(fmt(r, y), xy=(x, y), xytext=(x + 0.6, yy), color=INK, fontsize=8.5, va='center',
                    arrowprops=dict(arrowstyle='-', color=COL[r], lw=0.8) if abs(yy - y) > 1e-9 else None)

P, _ = route_profiles('case1')
# ---------------------------------------------------------------- fig1 age profile
f, ax = fig_new()
for r in ROUTES:
    p = P[r].copy(); p[p == 0] = np.nan
    ax.plot(AGES, p, color=COL[r], lw=2, ls=LS[r], label=LABEL[r], solid_capstyle='round')
ax.set_xlim(15, 69); ax.set_ylim(0, 11.5)
ax.set_xlabel('年齢', color=INK2, fontsize=9); ax.set_ylabel('年収（百万円, 2026年水準, 額面）', color=INK2, fontsize=9)
ax.set_title('図1 年齢別の年収カーブ（ケース1：典型的な卒業生・男性正社員）', color=INK, fontsize=11, loc='left')
end_labels(ax, {r: P[r][AGES == 59][0] for r in ROUTES}, 59.3, lambda r, y: f'{LABEL[r]} {y:.1f}')
ax.axvline(60, color='#b9b8b3', lw=0.8, ls=':'); ax.text(60.2, 0.5, '60歳 定年・再雇用', color=INK2, fontsize=7.5)
ax.legend(loc='upper left', frameon=False, fontsize=8.5, ncol=2)
f.text(0.01, 0.005, '出典: 厚労省 令和7年賃金構造基本統計調査, 総務省 令和4年就業構造基本調査, 文科省 令和7年度学校基本調査 等をもとに推計。C は D×1.065（国立大中心の仮定）。',
       fontsize=6.5, color=INK2)
f.tight_layout(rect=(0, 0.02, 1, 1)); f.savefig(os.path.join(OUT, 'fig1_age_profile.png')); plt.close(f)

# ---------------------------------------------------------------- fig2 cumulative (net of direct tuition)
f, ax = fig_new()
cum = {}
for r in ROUTES:
    c = np.cumsum(P[r] - cost_profile(r)); cum[r] = c
    ax.plot(AGES, c, color=COL[r], lw=2, ls=LS[r], label=LABEL[r])
ax.set_xlim(15, 70); ax.set_ylim(-10, 360)
ax.set_xlabel('年齢', color=INK2, fontsize=9); ax.set_ylabel('累積額（百万円, 学費控除後, 退職金除く）', color=INK2, fontsize=9)
ax.set_title('図2 15歳からの累積所得（直接学費を差し引き）と逆転年齢', color=INK, fontsize=11, loc='left')
end_labels(ax, {r: cum[r][-1] for r in ROUTES}, 64.3, lambda r, y: f'{LABEL[r]} {y:.0f}')
import analysis as AN
cr = AN.R['crossover']
marks = [('A', 'B', 'case1:A->B'), ('A', 'D', 'case1:A->D'), ('A', 'C', 'case1:A->C'), ('B', 'C', 'case1:B->C')]
for e, l, k in marks:
    age = cr[k]['net_of_tuition']
    if age:
        y = cum[l][AGES == age][0]
        ax.plot([age], [y], marker='o', ms=6, mfc=SURFACE, mec=INK, mew=1.2, zorder=5)
        ax.annotate(f'{e}→{l} 逆転 {age}歳', xy=(age, y), xytext=(age + 3.5, y - 48),
                    fontsize=8, color=INK, arrowprops=dict(arrowstyle='-', color=INK2, lw=0.7, shrinkA=0, shrinkB=4))
ax.text(51, 8, 'B→D は65歳までに逆転しない', fontsize=8, color=INK2)
ax.legend(loc='upper left', frameon=False, fontsize=8.5)
f.tight_layout(); f.savefig(os.path.join(OUT, 'fig2_cumulative.png')); plt.close(f)

# ---------------------------------------------------------------- fig3 lifetime totals by case (small multiples, shared x)
caseinfo = [('case1', 'ケース1 典型的な卒業生'), ('case2', 'ケース2 従業員1000人以上'), ('case3', 'ケース3 情報通信業（IT）')]
f, axes = plt.subplots(1, 3, figsize=(10.5, 3.9), dpi=200, sharey=True); f.patch.set_facecolor(SURFACE)
for ax, (c, title) in zip(axes, caseinfo):
    style(ax); ax.grid(axis='y', visible=False); ax.grid(axis='x', color=GRID, linewidth=0.8)
    S = AN.cases[c][2]
    ys = np.arange(4)[::-1]
    for y, r in zip(ys, ROUTES):
        v = S.loc[NAMES[r], '累積額面(〜64歳,平均)']; rt = S.loc[NAMES[r], '退職金']
        ax.barh(y, v, height=0.62, color=COL[r], edgecolor=SURFACE, linewidth=2)
        ax.barh(y, rt, left=v, height=0.62, color=COL[r], alpha=0.35, edgecolor=SURFACE, linewidth=2)
        ax.text(v + rt + 4, y, f'{v + rt:.0f}', va='center', fontsize=8.5, color=INK)
    ax.set_yticks(ys); ax.set_yticklabels([LABEL[r] for r in ROUTES], fontsize=8.5, color=INK)
    ax.set_xlim(0, 450); ax.set_title(title, fontsize=9.5, color=INK, loc='left')
    ax.set_xlabel('百万円（濃色=賃金18〜64歳, 淡色=退職金）', fontsize=7.5, color=INK2)
f.suptitle('図3 生涯賃金（退職金込み, 2026年水準）— ケース別', x=0.01, ha='left', fontsize=11, color=INK)
f.tight_layout(); f.savefig(os.path.join(OUT, 'fig3_cases.png')); plt.close(f)

# ---------------------------------------------------------------- fig4 sensitivity ranges (case1)
sens = AN.R['sensitivity']['case1']
f, ax = fig_new(8.6, 4.2); ax.grid(axis='y', visible=False); ax.grid(axis='x', color=GRID, linewidth=0.8)
ys = np.arange(4)[::-1]
for y, r in zip(ys, ROUTES):
    vals = [v[r]['total'] for k, v in sens.items() if '実質賃金' not in k]
    base = sens['基準(2026年水準・実質成長0%)'][r]['total']
    ax.plot([min(vals), max(vals)], [y, y], color=COL[r], lw=6, alpha=0.35, solid_capstyle='round')
    ax.plot([base], [y], marker='o', ms=8, color=COL[r], mec=SURFACE, mew=2)
    ax.text(max(vals) + 3, y, f'{min(vals):.0f}〜{max(vals):.0f}（基準 {base:.0f}）', va='center', fontsize=8.5, color=INK)
ax.set_yticks(ys); ax.set_yticklabels([LABEL[r] for r in ROUTES], fontsize=9, color=INK)
ax.set_xlim(240, 440); ax.set_xlabel('生涯賃金（退職金込み, 百万円, 実質成長0%）', fontsize=8.5, color=INK2)
ax.set_title('図4 感度分析の幅（ケース1）：転職・同一企業継続・役職定年/再雇用・理系プレミアム', fontsize=10.5, color=INK, loc='left')
f.tight_layout(); f.savefig(os.path.join(OUT, 'fig4_sensitivity.png')); plt.close(f)
print('saved to', OUT)
