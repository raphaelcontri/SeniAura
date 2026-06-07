"""
pdf_generator.py — SeniAura Dashboard PDF
═══════════════════════════════════════════════════════════════════════════════
Format  : A2 paysage (23.4 × 16.5 po) — zoomable, lisible
Layout  : Header · Contexte · [Tableau comparatif | Radar] · [Carte | Jumeaux | Leviers+Légende] · Footer
Fonts   : Scaled to PHYSICAL axes size → no overlap, no tiny text
═══════════════════════════════════════════════════════════════════════════════
"""

import os, re, time, io, math, textwrap
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

from ..data import BASE_DIR

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY    = '#1e3a5f'
BLUE    = '#2563eb'
SLATE   = '#334155'
LGRAY   = '#f1f5f9'
MGRAY   = '#e2e8f0'
DGRAY   = '#94a3b8'
RED     = '#b91c1c'
ORANGE  = '#c2410c'
TEAL    = '#0f766e'
CYAN    = '#0891b2'
WHITE   = '#ffffff'
LYELLOW = '#fffbeb'

EPCI_PALETTE = ['#1d4ed8', '#0f766e', '#b45309', '#7c2d12', '#5b21b6', '#0e7490']

PAGE_MAX = 6
FIG_W    = 23.4
FIG_H    = 16.5
DPI      = 150


# ── Helpers ───────────────────────────────────────────────────────────────────
def _ax_dims_pts(ax, fig):
    """Return (width_pts, height_pts) of an axes on the figure."""
    bbox = ax.get_position()
    fw, fh = fig.get_size_inches()
    return bbox.width * fw * 72, bbox.height * fh * 72


def _get_status(pct, sens):
    if sens == 1:
        if pct <= 10:  return "Alerte",     "⚠", RED,    True
        if pct <= 25:  return "Attention",  "!", ORANGE, True
        if pct >= 90:  return "Point fort", "✓", TEAL,   False
        if pct >= 75:  return "Atout",      "↑", CYAN,   False
        return "Médian", "─", DGRAY, False
    else:
        if pct >= 90:  return "Alerte",     "⚠", RED,    True
        if pct >= 75:  return "Attention",  "!", ORANGE, True
        if pct <= 10:  return "Point fort", "✓", TEAL,   False
        if pct <= 25:  return "Atout",      "↑", CYAN,   False
        return "Médian", "─", DGRAY, False


def get_action_levers_by_category():
    md_path = os.path.join(BASE_DIR, "Leviers d'action.md")
    if not os.path.exists(md_path):
        return {}
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {}
    lines = [l.strip() for l in content.strip().split('\n')]
    if len(lines) < 3:
        return {}
    headers = [h.strip() for h in lines[0].split('|')][1:-1]
    levers, cat = [], ''
    for line in lines[2:]:
        if not line:
            continue
        cols = [c.strip() for c in line.split('|')][1:-1]
        if len(cols) == len(headers):
            row = dict(zip(headers, cols))
            c = row.get('Catégorie', '').strip()
            if c:
                cat = c.replace('**', '').strip()
            row['Catégorie'] = cat
            levers.append(row)
    grouped = {}
    for lv in levers:
        raw = lv.get('Catégorie', '').lower()
        key = ('socio-économique' if 'socio' in raw
               else 'environnement' if 'env' in raw
               else 'santé')
        grouped.setdefault(key, []).append(lv)
    return grouped


def _strip_md(text):
    if not text or str(text).strip() == '':
        return '—'
    return re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', str(text))


def calculate_twins(gdf_merged, target_code, active_vars):
    if not target_code or not active_vars or len(active_vars) < 2:
        return []
    dept_col = next(
        (c for c in ['nom_dep', 'CODE_DEPT', 'dept_name', 'nom_dept']
         if c in gdf_merged.columns), None)
    cols = ['EPCI_CODE', 'nom_EPCI'] + active_vars + ([dept_col] if dept_col else [])
    df = gdf_merged[cols].copy()
    for v in active_vars:
        df[v] = pd.to_numeric(df[v], errors='coerce')
        med = df[v].median()
        df[v] = df[v].fillna(med if pd.notna(med) else 0.0)
    z = df[active_vars].copy()
    for v in active_vars:
        mu, sig = z[v].mean(), z[v].std()
        z[v] = (z[v] - mu) / (sig if sig != 0 else 1.0)
    tgt = df[df['EPCI_CODE'] == target_code]
    if tgt.empty:
        return []
    tgt_vec = z.loc[tgt.index[0]].values
    results = []
    for idx2, row2 in df.iterrows():
        if row2['EPCI_CODE'] == target_code:
            continue
        dist = float(np.sqrt(np.sum((tgt_vec - z.loc[idx2].values) ** 2)))
        dept = str(row2[dept_col]) if dept_col else '—'
        results.append({'nom': row2['nom_EPCI'], 'dept': dept, 'distance': dist})
    results.sort(key=lambda x: x['distance'])
    n = len(active_vars)
    for t in results[:3]:
        t['resemblance'] = 100.0 * float(np.exp(-t['distance'] / np.sqrt(n)))
    return results[:3]


# ═════════════════════════════════════════════════════════════════════════════
#   TABLE DRAWING — font sized from PHYSICAL axes dimensions
# ═════════════════════════════════════════════════════════════════════════════
def _draw_table(ax, fig, headers, rows, col_w,
                header_bg=NAVY,
                status_cols=None,
                bold_cols=None,
                title=None):
    """
    Manual table with fonts proportional to the physical cell size.
    col_w: list of fractions summing to 1.
    status_cols: {col_idx: [hex per row]}
    bold_cols: set of col indices
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor(WHITE)
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_edgecolor(MGRAY)

    if not rows:
        ax.text(0.5, 0.5, '—', ha='center', va='center',
                fontsize=12, color=DGRAY, transform=ax.transAxes)
        return

    # Physical dimensions of this axes
    ax_w_pts, ax_h_pts = _ax_dims_pts(ax, fig)

    # Layout
    title_frac = 0.06 if title else 0.0
    n_slots    = len(rows) + 1  # +1 header
    row_h_frac = (1.0 - title_frac) / n_slots
    row_h_pts  = row_h_frac * ax_h_pts

    # Font: Start with 45% of physical row height
    fs_max = row_h_pts * 0.45
    
    # Calculate required font size to fit ALL text without truncation
    # char_w ≈ fs * 0.55 => fs ≈ char_w / 0.55
    # We want max_len * fs * 0.55 <= w_frac * ax_w_pts * 0.95
    # fs <= (w_frac * ax_w_pts * 0.95) / (max_len * 0.55)
    fs_fit = 100
    for j, w in enumerate(col_w):
        texts = [headers[j]] + [r[j] for r in rows]
        # split multiline strings to get max line length
        max_l = max(max((len(line) for line in str(t).split('\n')), default=1) for t in texts)
        if max_l == 0: max_l = 1
        fs_col = (w * ax_w_pts * 0.92) / (max_l * 0.55)
        if fs_col < fs_fit:
            fs_fit = fs_col

    fs = max(6, min(fs_max, fs_fit))
    fs_hdr = fs * 0.95

    # Title
    if title:
        title_fs = max(9, min(20, title_frac * ax_h_pts * 0.55))
        ax.text(0.005, 1.0 - title_frac * 0.5, title,
                transform=ax.transAxes, fontsize=title_fs,
                fontweight='bold', color=NAVY, va='center', clip_on=True)

    content_top = 1.0 - title_frac

    def _max_chars(w_frac):
        """Estimate max characters that fit in a column at current font size."""
        col_pts = w_frac * ax_w_pts
        char_w  = fs * 0.55  # average char width ≈ 0.55 × font size
        return max(3, int(col_pts / char_w))

    def _trunc(s, w_frac):
        mc = _max_chars(w_frac)
        lines = str(s).split('\n')
        out = []
        for line in lines:
            out.append((line[:mc - 1] + '…') if len(line) > mc else line)
        return '\n'.join(out)

    # Header row
    x = 0.0
    for j, (hdr, w) in enumerate(zip(headers, col_w)):
        ax.add_patch(Rectangle(
            (x, content_top - row_h_frac), w - 0.001, row_h_frac * 0.98,
            facecolor=header_bg, edgecolor='none',
            transform=ax.transAxes, clip_on=True))
        ax.text(x + 0.006, content_top - row_h_frac * 0.5,
                _trunc(hdr, w),
                transform=ax.transAxes, fontsize=fs_hdr,
                fontweight='bold', color='white',
                va='center', ha='left', clip_on=True)
        x += w

    # Data rows
    for r, row_data in enumerate(rows):
        y_top = content_top - (r + 1) * row_h_frac
        y_bot = y_top - row_h_frac
        bg    = LGRAY if r % 2 == 0 else WHITE
        x = 0.0
        for j, (cell, w) in enumerate(zip(row_data, col_w)):
            ax.add_patch(Rectangle(
                (x, y_bot), w - 0.001, row_h_frac * 0.97,
                facecolor=bg, edgecolor='none',
                transform=ax.transAxes, clip_on=True))
            tc = SLATE
            fw = 'bold' if (bold_cols and j in bold_cols) else 'normal'
            if status_cols and j in status_cols:
                tc = status_cols[j][r]
                if tc in (RED, ORANGE):
                    fw = 'bold'
            ax.text(x + 0.006, y_bot + row_h_frac * 0.47,
                    _trunc(cell, w),
                    transform=ax.transAxes, fontsize=fs,
                    color=tc, fontweight=fw,
                    va='center', ha='left', clip_on=True)
            x += w
        # Row separator
        ax.plot([0, 1], [y_bot, y_bot], color=MGRAY, linewidth=0.3,
                transform=ax.transAxes, clip_on=True)


# ═════════════════════════════════════════════════════════════════════════════
#   COMPARISON TABLE
# ═════════════════════════════════════════════════════════════════════════════
def _draw_comparison_table(ax, fig, epci_codes, epci_names, selected_vars,
                            gdf_merged, variable_dict, unit_dict, sens_dict,
                            category_dict, ranks_df):
    n_epci = len(epci_codes)
    ind_w  = 0.30
    mean_w = 0.08
    epci_w = round((1.0 - ind_w - mean_w) / n_epci, 6)

    ax_w_pts, _ = _ax_dims_pts(ax, fig)
    col_pts     = epci_w * ax_w_pts
    est_chars   = max(5, int(col_pts / (10 * 0.55)))  # rough char estimate at ~10pt
    short_names = [(n[:est_chars - 1] + '…') if len(n) > est_chars else n
                   for n in epci_names]

    headers    = ['Indicateur'] + short_names + ['Moy. rég.']
    col_widths = [ind_w] + [epci_w] * n_epci + [mean_w]
    rows, status_cols, prim_levers = [], {j + 1: [] for j in range(n_epci)}, []

    # Wrap the indicator text so it fits well without making the font tiny
    ind_col_pts = ind_w * ax_w_pts
    wrap_width = max(15, int(ind_col_pts / (9 * 0.55)))  # assume ~9pt font for wrapping

    for v in selected_vars:
        label = variable_dict.get(v, v) or v
        label = textwrap.fill(label, width=wrap_width)
        unit  = unit_dict.get(v, '')
        avg   = gdf_merged[v].mean()
        avg_s = (f"{avg:.1f}{' ' + unit if unit else ''}") if pd.notna(avg) else 'N/D'
        row_cells = [label]
        for j, code in enumerate(epci_codes):
            r = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if r.empty:
                row_cells.append('N/D')
                status_cols[j + 1].append(DGRAY)
                continue
            ri  = r.index[0]
            val = r[v].values[0]
            val_s = (f"{val:.1f}{' ' + unit if unit else ''}") if pd.notna(val) else 'N/D'
            pct = ranks_df.loc[ri, v] * 100
            sens = sens_dict.get(v, -1)
            _, sym, sc, is_vuln = _get_status(pct, sens)
            row_cells.append(f"{val_s} {sym}")
            status_cols[j + 1].append(sc)
            if is_vuln and j == 0:
                cat_raw = category_dict.get(v, '').lower()
                cat_key = ('socio-économique' if 'socio' in cat_raw
                           else 'environnement' if 'env' in cat_raw
                           else 'santé')
                if cat_key not in prim_levers:
                    prim_levers.append(cat_key)
        row_cells.append(avg_s)
        rows.append(row_cells)

    _draw_table(
        ax, fig, headers, rows, col_widths,
        header_bg=NAVY, status_cols=status_cols,
        bold_cols={1 + j for j in range(n_epci)},
        title='Tableau comparatif — Positionnement régional (percentile · AuRA)',
    )
    return prim_levers


# ═════════════════════════════════════════════════════════════════════════════
#   RADAR (combined, all EPCIs)
# ═════════════════════════════════════════════════════════════════════════════
def _draw_radar(ax, fig, gdf_merged, selected_vars, epci_codes, epci_names,
                variable_dict, ranks_df):
    n = len(selected_vars)
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    tick_fs = max(6, min(11, ax_h_pts / 55))
    title_fs = max(8, min(14, ax_h_pts / 40))

    if n < 3:
        ax.axis('off')
        ax.text(0.5, 0.5, 'Sélectionner ≥ 3 indicateurs\npour le radar.',
                ha='center', va='center', fontsize=tick_fs + 1, color=DGRAY,
                transform=ax.transAxes, style='italic', multialignment='center')
        return

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    ax.set_facecolor('#f8fafc')
    ax.grid(color=MGRAY, linestyle='-', linewidth=0.4, alpha=0.7)
    ax.spines['polar'].set_color(MGRAY)
    ax.spines['polar'].set_linewidth(0.5)

    labels = [(variable_dict.get(v, v) or v) for v in selected_vars]
    lbl_max = max(8, int(tick_fs * 1.8))
    labels_s = [(lb[:lbl_max - 1] + '…') if len(lb) > lbl_max else lb for lb in labels]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_s, fontsize=tick_fs, color=SLATE, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75])
    ax.set_yticklabels(['25 %', '50 %', '75 %'], fontsize=tick_fs * 0.7, color=DGRAY)

    ax.fill(angles, [50] * (n + 1), color=MGRAY, alpha=0.30, linewidth=0,
            label='Médiane rég.')

    for i, (code, name) in enumerate(zip(epci_codes, epci_names)):
        row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
        if row.empty:
            continue
        ri   = row.index[0]
        vals = [ranks_df.loc[ri, v] * 100 for v in selected_vars]
        vals += vals[:1]
        col  = EPCI_PALETTE[i % len(EPCI_PALETTE)]
        short = (name[:20] + '…') if len(name) > 21 else name
        ax.plot(angles, vals, color=col, linewidth=2.2, label=short, zorder=3)
        ax.fill(angles, vals, color=col, alpha=0.10, zorder=2)

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12),
              fontsize=tick_fs * 0.85, frameon=True, fancybox=True,
              edgecolor=MGRAY, framealpha=0.9, ncol=2)
    ax.set_title('Profil radar comparatif\n(percentiles régionaux)',
                 fontsize=title_fs, fontweight='bold', color=NAVY, pad=12)


# ═════════════════════════════════════════════════════════════════════════════
#   MAP
# ═════════════════════════════════════════════════════════════════════════════
def _draw_map(ax, fig, gdf_merged, target_var, epci_codes, label_name, epci_names):
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    fs = max(7, min(12, ax_h_pts / 40))

    ax.set_facecolor('#f8fafc')
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_edgecolor(MGRAY)
    try:
        gdf_merged.plot(
            column=target_var, cmap='Blues', legend=False, ax=ax,
            edgecolor='#d1d5db', linewidth=0.12,
            missing_kwds={'color': '#f0f4f8', 'edgecolor': '#e2e8f0'}
        )
        for i, code in enumerate(epci_codes):
            sel = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if not sel.empty:
                sel.plot(ax=ax, facecolor='none',
                         edgecolor=EPCI_PALETTE[i % len(EPCI_PALETTE)], linewidth=2.5)
    except Exception:
        ax.text(0.5, 0.5, 'Carte indisponible',
                ha='center', va='center', fontsize=fs, color=DGRAY,
                transform=ax.transAxes)
    ax.set_axis_off()
    short_lbl = (label_name[:35] + '…') if len(label_name) > 36 else label_name
    ax.set_title(f'Carte régionale — {short_lbl}', fontsize=fs * 1.15,
                 fontweight='bold', color=NAVY, pad=6)
    for i, name in enumerate(epci_names):
        col = EPCI_PALETTE[i % len(EPCI_PALETTE)]
        short = (name[:22] + '…') if len(name) > 23 else name
        ax.text(0.02, 0.04 + i * 0.06, f'■ {short}',
                transform=ax.transAxes, fontsize=fs * 0.85,
                color=col, fontweight='bold', va='bottom', clip_on=True)


# ═════════════════════════════════════════════════════════════════════════════
#   TWINS (prominent cards with progress bars)
# ═════════════════════════════════════════════════════════════════════════════
def _draw_twins(ax, fig, twins, primary_name):
    ax_w_pts, ax_h_pts = _ax_dims_pts(ax, fig)
    fs      = max(8, min(14, ax_h_pts / 35))
    fs_sm   = fs * 0.8
    fs_title = fs * 1.2

    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.7)
        sp.set_edgecolor('#93c5fd')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    short_p = (primary_name[:30] + '…') if len(primary_name) > 31 else primary_name
    ax.text(0.02, 0.96, '🔗  Territoires jumeaux',
            transform=ax.transAxes, fontsize=fs_title,
            fontweight='bold', color=NAVY, va='top', clip_on=True)
    ax.text(0.02, 0.88, f"Référence : {short_p}  ·  profils les plus proches (AuRA)",
            transform=ax.transAxes, fontsize=fs_sm, color=SLATE,
            va='top', style='italic', clip_on=True)

    if not twins:
        ax.text(0.5, 0.45, '≥ 2 indicateurs requis pour le benchmark.',
                ha='center', va='center', fontsize=fs, color=DGRAY,
                transform=ax.transAxes, style='italic')
        return

    card_h = 0.22
    gap    = 0.04

    for i, t in enumerate(twins):
        y_top = 0.78 - i * (card_h + gap)
        y_mid = y_top - card_h * 0.5
        res   = t['resemblance']
        col   = TEAL if res >= 80 else (BLUE if res >= 65 else ORANGE)

        # Card background
        ax.add_patch(FancyBboxPatch(
            (0.02, y_top - card_h), 0.96, card_h,
            boxstyle='round,pad=0.008',
            facecolor=WHITE, edgecolor=col, linewidth=1.2,
            transform=ax.transAxes, clip_on=True))

        # Rank badge
        ax.text(0.06, y_mid, f"#{i + 1}",
                transform=ax.transAxes, fontsize=fs * 1.3, fontweight='bold',
                color=col, va='center', ha='center', clip_on=True)

        # Twin name
        mc = max(10, int((ax_w_pts * 0.45) / (fs * 0.55)))
        tname = t['nom']
        tname = (tname[:mc - 1] + '…') if len(tname) > mc else tname
        ax.text(0.12, y_top - card_h * 0.28, tname,
                transform=ax.transAxes, fontsize=fs,
                fontweight='bold', color=NAVY, va='center', clip_on=True)

        ax.text(0.12, y_top - card_h * 0.70, f"Dép. : {t['dept']}",
                transform=ax.transAxes, fontsize=fs_sm, color=SLATE,
                va='center', clip_on=True)

        # Progress bar
        bar_x, bar_w_max, bar_h = 0.58, 0.32, card_h * 0.30
        bar_w = bar_w_max * min(res, 100) / 100
        ax.add_patch(Rectangle(
            (bar_x, y_mid - bar_h * 0.5), bar_w_max, bar_h,
            facecolor='#e0f2fe', edgecolor='none',
            transform=ax.transAxes, clip_on=True))
        ax.add_patch(Rectangle(
            (bar_x, y_mid - bar_h * 0.5), bar_w, bar_h,
            facecolor=col, edgecolor='none',
            transform=ax.transAxes, clip_on=True))
        ax.text(bar_x + bar_w_max + 0.015, y_mid,
                f"{res:.1f} %",
                transform=ax.transAxes, fontsize=fs,
                fontweight='bold', color=col, va='center', clip_on=True)


# ═════════════════════════════════════════════════════════════════════════════
#   LEVERS
# ═════════════════════════════════════════════════════════════════════════════
def _draw_levers(ax, fig, suggested_levers, all_levers, primary_name):
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    fs   = max(7, min(12, ax_h_pts / 30))
    fs_t = fs * 1.1

    ax.set_facecolor(LYELLOW)
    ax.axis('off')
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.7)
        sp.set_edgecolor('#fbbf24')
        
    short_p = (primary_name[:35] + '…') if len(primary_name) > 36 else primary_name
    ax.set_title(f"Leviers d'action prioritaires\n(pour : {short_p})", fontsize=fs_t,
                 fontweight='bold', color='#92400e', pad=6, loc='left')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if not suggested_levers:
        ax.text(0.04, 0.5, 'Aucune vulnérabilité prioritaire détectée.',
                transform=ax.transAxes, fontsize=fs, color=TEAL,
                va='center', style='italic')
        return

    y    = 0.90
    line = 1.5 / max(1, ax_h_pts / fs)  # line height in axes fraction

    for cat_key in suggested_levers[:2]:
        m = all_levers.get(cat_key, [])
        if not m:
            continue
        ax.text(0.02, y, f'▸  {cat_key.capitalize()}',
                transform=ax.transAxes, fontsize=fs,
                fontweight='bold', color=NAVY, va='top', clip_on=True)
        y -= line * 1.2
        for lv in m[:3]:
            t = _strip_md(lv.get("Levier d'action", ''))
            s = lv.get('Source', '—')
            mc = max(10, int(0.9 * ax_h_pts / (fs * 0.07)))  # rough chars
            t = (t[:mc] + '…') if len(t) > mc else t
            txt = f'  • {t}  [{s}]'
            ax.text(0.02, y, txt, transform=ax.transAxes, fontsize=fs * 0.88,
                    color=SLATE, va='top', clip_on=True)
            y -= line * 1.1
            if y < 0.04:
                break
        y -= line * 0.5
        if y < 0.04:
            break


# ═════════════════════════════════════════════════════════════════════════════
#   LEGEND
# ═════════════════════════════════════════════════════════════════════════════
def _draw_legend(ax, fig):
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    fs = max(7, min(12, ax_h_pts / 22))

    ax.set_facecolor(LGRAY)
    ax.axis('off')
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.4)
        sp.set_edgecolor(MGRAY)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.06, 0.94, 'Légende — Positionnement',
            transform=ax.transAxes, fontsize=fs * 1.05, fontweight='bold',
            color=NAVY, va='top', clip_on=True)
    items = [
        ("⚠ Alerte",     RED,    "10 % les + défavorables"),
        ("!  Attention",  ORANGE, "25 % les + défavorables"),
        ("✓ Point fort",  TEAL,   "10 % les + favorables"),
        ("↑  Atout",      CYAN,   "25 % les + favorables"),
        ("─  Médian",     DGRAY,  "dans la moyenne"),
    ]
    spacing = min(0.155, 0.78 / len(items))
    y = 0.78
    for lbl, col, desc in items:
        ax.text(0.06, y, lbl, transform=ax.transAxes, fontsize=fs,
                fontweight='bold', color=col, va='center', clip_on=True)
        ax.text(0.48, y, desc, transform=ax.transAxes, fontsize=fs * 0.9,
                color=SLATE, va='center', clip_on=True)
        y -= spacing


# ═════════════════════════════════════════════════════════════════════════════
#   CONTEXT
# ═════════════════════════════════════════════════════════════════════════════
def _draw_context(ax, fig, epci_names, selected_vars, variable_dict, category_dict):
    ax_w_pts, ax_h_pts = _ax_dims_pts(ax, fig)
    fs = max(8, min(13, ax_h_pts / 5.5))

    cats = set()
    for v in selected_vars:
        c = category_dict.get(v, '').lower()
        cats.add('socio-économique' if 'socio' in c else 'environnementale' if 'env' in c else 'sanitaire')
    cats_str = ', '.join(sorted(cats)) if cats else 'sanitaire'

    n = len(epci_names)
    if n == 1:
        terr = epci_names[0]
    elif n <= 3:
        terr = ' / '.join(epci_names)
    else:
        terr = f"{n} territoires sélectionnés"

    txt = (
        f"Analyse de {terr}  ·  {len(selected_vars)} indicateurs ({cats_str})  ·  "
        f"Positionnement vs. ensemble des EPCI AuRA  ·  "
        f"Jumeaux et leviers calculés pour : {epci_names[0]}"
    )

    ax.set_facecolor('#eff6ff')
    ax.axis('off')
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_edgecolor('#bfdbfe')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.008, 0.62, f'📋  {txt}',
            transform=ax.transAxes, fontsize=fs,
            color=SLATE, va='center', ha='left', clip_on=True)


# ═════════════════════════════════════════════════════════════════════════════
#   HEADER + FOOTER
# ═════════════════════════════════════════════════════════════════════════════
def _draw_header(ax, fig, epci_names, date_str, n_vars):
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    fs_big = max(10, min(18, ax_h_pts * 0.40))
    fs_sm  = fs_big * 0.65

    ax.set_facecolor(NAVY)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axhline(0, color=BLUE, linewidth=3.5)

    n = len(epci_names)
    if n == 1:
        title = epci_names[0]
    elif n <= 4:
        title = '  ·  '.join(epci_names)
    else:
        title = '  ·  '.join(epci_names[:3]) + f'  (+ {n - 3})'
    ax.text(0.008, 0.65, title, color='white', fontsize=fs_big,
            fontweight='bold', va='center', ha='left', clip_on=True)
    ax.text(0.008, 0.22,
            f"Diagnostic territorial · Auvergne-Rhône-Alpes · {n_vars} indicateurs",
            color='#93c5fd', fontsize=fs_sm, va='center', ha='left')
    ax.text(0.992, 0.45, f"SeniAura Analytics · {date_str}",
            color='#93c5fd', fontsize=fs_sm, va='center', ha='right')


def _draw_footer(ax, fig, page_num, total):
    _, ax_h_pts = _ax_dims_pts(ax, fig)
    fs = max(6, min(10, ax_h_pts * 0.38))

    ax.set_facecolor(LGRAY)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axhline(1, color=MGRAY, linewidth=0.6)
    ax.text(0.008, 0.5,
            'SeniAura Analytics  ·  ARS Auvergne-Rhône-Alpes  ·  Usage interne',
            color=DGRAY, fontsize=fs, va='center')
    ax.text(0.992, 0.5, f'Page {page_num} / {total}',
            color=DGRAY, fontsize=fs, va='center', ha='right')


# ═════════════════════════════════════════════════════════════════════════════
#   PAGE BUILDER
# ═════════════════════════════════════════════════════════════════════════════
def _build_page(epci_codes_page, gdf_merged, selected_vars,
                variable_dict, unit_dict, sens_dict, category_dict,
                ranks_df, all_levers, page_num, total_pages):
    """
    Layout (height fractions):
      [0] header    5 %
      [1] context   5 %
      [2] main     50 %  ← table 60% | radar 40%
      [3] analysis 37 %  ← map 30% | twins 40% | levers 18% | legend 12%
      [4] footer    3 %
    """
    epci_names, valid_codes = [], []
    for code in epci_codes_page:
        r = gdf_merged[gdf_merged['EPCI_CODE'] == code]
        if r.empty:
            continue
        epci_names.append(r['nom_EPCI'].values[0])
        valid_codes.append(code)
    if not valid_codes:
        return None

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor='white', dpi=DPI)

    gs = gridspec.GridSpec(
        5, 1, figure=fig,
        left=0.008, right=0.992, bottom=0.006, top=0.994,
        hspace=0.012,
        height_ratios=[0.05, 0.05, 0.50, 0.37, 0.03]
    )

    # [0] Header
    ax_hdr = fig.add_subplot(gs[0])
    _draw_header(ax_hdr, fig, epci_names, time.strftime('%d/%m/%Y'), len(selected_vars))

    # [1] Context
    ax_ctx = fig.add_subplot(gs[1])
    _draw_context(ax_ctx, fig, epci_names, selected_vars, variable_dict, category_dict)

    # [2] Main: table | radar
    gs_main = gridspec.GridSpecFromSubplotSpec(
        1, 2, subplot_spec=gs[2], wspace=0.04,
        width_ratios=[0.60, 0.40])
    ax_table = fig.add_subplot(gs_main[0])
    ax_radar = fig.add_subplot(gs_main[1], projection='polar')

    prim_levers = _draw_comparison_table(
        ax_table, fig, valid_codes, epci_names, selected_vars,
        gdf_merged, variable_dict, unit_dict, sens_dict,
        category_dict, ranks_df)
    _draw_radar(ax_radar, fig, gdf_merged, selected_vars,
                valid_codes, epci_names, variable_dict, ranks_df)

    # [3] Analysis: map | twins | levers | legend
    gs_ana = gridspec.GridSpecFromSubplotSpec(
        1, 4, subplot_spec=gs[3], wspace=0.04,
        width_ratios=[0.28, 0.38, 0.20, 0.14])
    ax_map    = fig.add_subplot(gs_ana[0])
    ax_twins  = fig.add_subplot(gs_ana[1])
    ax_levers = fig.add_subplot(gs_ana[2])
    ax_legend = fig.add_subplot(gs_ana[3])

    primary_var = selected_vars[0] if selected_vars else None
    if primary_var:
        pname = variable_dict.get(primary_var, primary_var)
        punit = unit_dict.get(primary_var, '')
        lbl = f'{pname} ({punit})' if punit else pname
        _draw_map(ax_map, fig, gdf_merged, primary_var, valid_codes, lbl, epci_names)
    else:
        ax_map.axis('off')

    twins = calculate_twins(gdf_merged, valid_codes[0], selected_vars)
    _draw_twins(ax_twins, fig, twins, epci_names[0])
    _draw_levers(ax_levers, fig, prim_levers, all_levers, epci_names[0])
    _draw_legend(ax_legend, fig)

    # [4] Footer
    ax_ftr = fig.add_subplot(gs[4])
    _draw_footer(ax_ftr, fig, page_num, total_pages)

    return fig


# ═════════════════════════════════════════════════════════════════════════════
#   PUBLIC ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════
def generate_territory_pdf(epci_codes, selected_vars, gdf_merged,
                            variable_dict, unit_dict, sens_dict, category_dict):
    buffer     = io.BytesIO()
    all_levers = get_action_levers_by_category()
    ranks_df   = gdf_merged[selected_vars].rank(pct=True)

    valid_codes = [c for c in epci_codes
                   if not gdf_merged[gdf_merged['EPCI_CODE'] == c].empty]
    if not valid_codes:
        with PdfPages(buffer) as pdf:
            fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor='white')
            fig.text(0.5, 0.5, 'Aucun territoire valide sélectionné.',
                     ha='center', va='center', fontsize=18, color=DGRAY)
            pdf.savefig(fig, dpi=DPI, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
        buffer.seek(0)
        return buffer

    pages = [valid_codes[i:i + PAGE_MAX]
             for i in range(0, len(valid_codes), PAGE_MAX)]

    with PdfPages(buffer) as pdf:
        d = pdf.infodict()
        d['Title']  = 'Diagnostic Territorial — AuRA'
        d['Author'] = 'SeniAura Analytics'

        for pn, pc in enumerate(pages, 1):
            fig = _build_page(
                pc, gdf_merged, selected_vars,
                variable_dict, unit_dict, sens_dict, category_dict,
                ranks_df, all_levers, pn, len(pages))
            if fig is None:
                continue
            pdf.savefig(fig, dpi=DPI, bbox_inches='tight', pad_inches=0)
            plt.close(fig)

    buffer.seek(0)
    return buffer
