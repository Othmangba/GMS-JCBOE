#!/usr/bin/env python3
"""
generate_pdf_report.py
Converts FINDINGS_REPORT.md into a professionally branded OCC Research PDF.
Uses markdown + weasyprint for HTML-to-PDF conversion.
"""

import markdown
from weasyprint import HTML
from pathlib import Path
import re
import datetime

REPORT_MD = Path(__file__).parent / "FINDINGS_REPORT.md"
OUTPUT_PDF = Path.home() / "Desktop" / "occ-research-website" / "public" / "gms-jcboe-report.pdf"

# OCC Research branding colors
NAVY = "#0B1628"
CYAN = "#00D4FF"
GOLD = "#E8A838"
BODY_TEXT = "#2D2D2D"
LIGHT_GRAY = "#F5F6F8"
MID_GRAY = "#E0E0E0"
TABLE_HEADER_BG = "#0B1628"
TABLE_ALT_ROW = "#F0F4F8"

# SVG logo: scope/crosshair with center dot
LOGO_SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <circle cx="24" cy="24" r="18" stroke="{CYAN}" stroke-width="2.5" fill="none"/>
  <line x1="24" y1="2" x2="24" y2="14" stroke="{CYAN}" stroke-width="2"/>
  <line x1="24" y1="34" x2="24" y2="46" stroke="{CYAN}" stroke-width="2"/>
  <line x1="2" y1="24" x2="14" y2="24" stroke="{CYAN}" stroke-width="2"/>
  <line x1="34" y1="24" x2="46" y2="24" stroke="{CYAN}" stroke-width="2"/>
  <circle cx="24" cy="24" r="3.5" fill="{CYAN}"/>
</svg>'''

# Inline the SVG as a data URI for use in CSS/HTML
import base64
LOGO_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG.encode()).decode()


def build_cover_page():
    """Generate the cover page HTML."""
    today = datetime.date.today().strftime("%B %Y")
    return f'''
    <div class="cover-page">
        <div class="cover-logo">
            {LOGO_SVG}
        </div>
        <div class="cover-org">OCC Research</div>
        <div class="cover-tagline">Governance Memory System (GMS)</div>
        <div class="cover-divider"></div>
        <h1 class="cover-title">Where Did the Money Go?</h1>
        <p class="cover-subtitle">A GMS Investigation into Jersey City Board of Education<br>Contract Transparency</p>
        <div class="cover-meta">
            <p class="cover-date">{today}</p>
            <p class="cover-author">Othman Gbadamassi</p>
            <p class="cover-org-line">OCC Research &middot; occresearch.org</p>
        </div>
    </div>
    '''


def build_toc(headings):
    """Generate a table of contents from extracted headings."""
    toc_html = '<div class="toc-page"><h2 class="toc-title">Table of Contents</h2><ul class="toc-list">'
    for level, text, anchor in headings:
        indent_class = f"toc-level-{level}"
        toc_html += f'<li class="{indent_class}"><a href="#{anchor}">{text}</a></li>'
    toc_html += '</ul></div>'
    return toc_html


def extract_headings(md_text):
    """Extract h2 and h3 headings from markdown for TOC."""
    headings = []
    for line in md_text.split('\n'):
        m = re.match(r'^(#{2,3})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            # Skip the title line and "How to Read" since they're on cover/early pages
            if text.startswith("A GMS Investigation"):
                continue
            anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            headings.append((level, text, anchor))
    return headings


def convert_md_to_html(md_text):
    """Convert markdown to HTML with extensions."""
    extensions = ['tables', 'fenced_code', 'toc', 'smarty']
    extension_configs = {
        'toc': {
            'permalink': False,
            'slugify': lambda value, separator: re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-'),
        }
    }
    html = markdown.markdown(md_text, extensions=extensions, extension_configs=extension_configs)
    return html


def build_css():
    """Return the full CSS stylesheet for the PDF."""
    return f'''
    @page {{
        size: letter;
        margin: 1in 0.85in 1in 0.85in;
        @bottom-center {{
            content: "OCC Research  |  occresearch.org";
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 8pt;
            color: #999;
        }}
        @bottom-right {{
            content: counter(page);
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 8pt;
            color: #999;
        }}
    }}

    @page :first {{
        margin: 0;
        @bottom-center {{ content: none; }}
        @bottom-right {{ content: none; }}
    }}

    /* ---- Cover page ---- */
    .cover-page {{
        page-break-after: always;
        width: 8.5in;
        height: 11in;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 2in 1.2in;
        box-sizing: border-box;
        background: white;
    }}
    .cover-logo svg {{
        width: 72px;
        height: 72px;
        margin-bottom: 12px;
    }}
    .cover-org {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 28pt;
        font-weight: bold;
        color: {NAVY};
        letter-spacing: 1px;
        margin-bottom: 4px;
    }}
    .cover-tagline {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 11pt;
        color: {CYAN};
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 24px;
    }}
    .cover-divider {{
        width: 80px;
        height: 3px;
        background: {CYAN};
        margin: 16px auto 32px auto;
    }}
    .cover-title {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 32pt;
        font-weight: bold;
        color: {NAVY};
        margin: 0 0 16px 0;
        line-height: 1.15;
    }}
    .cover-subtitle {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 14pt;
        color: {BODY_TEXT};
        line-height: 1.5;
        margin-bottom: 48px;
    }}
    .cover-meta {{
        margin-top: auto;
    }}
    .cover-date {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 12pt;
        color: {BODY_TEXT};
        margin: 4px 0;
    }}
    .cover-author {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 12pt;
        font-weight: bold;
        color: {NAVY};
        margin: 4px 0;
    }}
    .cover-org-line {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 10pt;
        color: #888;
        margin: 4px 0;
    }}

    /* ---- TOC page ---- */
    .toc-page {{
        page-break-after: always;
        padding-top: 0.5in;
    }}
    .toc-title {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 22pt;
        color: {NAVY};
        border-bottom: 3px solid {CYAN};
        padding-bottom: 8px;
        margin-bottom: 20px;
    }}
    .toc-list {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}
    .toc-list li {{
        margin: 0;
        padding: 6px 0;
        border-bottom: 1px solid #eee;
    }}
    .toc-list li a {{
        text-decoration: none;
        color: {NAVY};
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 11pt;
    }}
    .toc-level-2 {{
        padding-left: 0 !important;
        font-weight: bold;
    }}
    .toc-level-2 a {{
        font-weight: bold !important;
    }}
    .toc-level-3 {{
        padding-left: 20px !important;
    }}
    .toc-level-3 a {{
        font-weight: normal !important;
        color: #555 !important;
        font-size: 10pt !important;
    }}

    /* ---- Body ---- */
    body {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 10.5pt;
        line-height: 1.6;
        color: {BODY_TEXT};
        background: white;
    }}

    /* ---- Headings ---- */
    h1 {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 26pt;
        color: {NAVY};
        margin-top: 36px;
        margin-bottom: 8px;
        line-height: 1.2;
        page-break-after: avoid;
    }}
    h2 {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 18pt;
        color: {NAVY};
        margin-top: 28px;
        margin-bottom: 8px;
        padding-bottom: 4px;
        border-bottom: 2px solid {CYAN};
        page-break-after: avoid;
    }}
    h3 {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 13pt;
        color: {NAVY};
        margin-top: 20px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}
    h4 {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 11pt;
        color: {CYAN};
        margin-top: 16px;
        margin-bottom: 4px;
        page-break-after: avoid;
    }}

    /* ---- Paragraphs ---- */
    p {{
        margin: 8px 0;
        orphans: 3;
        widows: 3;
    }}

    /* ---- Strong / emphasis ---- */
    strong {{
        color: {NAVY};
    }}

    /* ---- Links ---- */
    a {{
        color: {CYAN};
        text-decoration: none;
    }}

    /* ---- Horizontal rules ---- */
    hr {{
        border: none;
        border-top: 1px solid {MID_GRAY};
        margin: 24px 0;
    }}

    /* ---- Tables ---- */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 9.5pt;
        page-break-inside: auto;
    }}
    thead {{
        display: table-header-group;
    }}
    tr {{
        page-break-inside: avoid;
    }}
    th {{
        background: {TABLE_HEADER_BG};
        color: white;
        font-weight: 600;
        text-align: left;
        padding: 8px 10px;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 9pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    td {{
        padding: 7px 10px;
        border-bottom: 1px solid {MID_GRAY};
        vertical-align: top;
    }}
    tr:nth-child(even) td {{
        background: {TABLE_ALT_ROW};
    }}

    /* ---- Blockquotes ---- */
    blockquote {{
        border-left: 4px solid {CYAN};
        margin: 16px 0;
        padding: 8px 16px;
        background: {LIGHT_GRAY};
        color: #444;
        font-style: italic;
    }}
    blockquote p {{
        margin: 4px 0;
    }}

    /* ---- Code blocks ---- */
    pre {{
        background: {LIGHT_GRAY};
        border: 1px solid {MID_GRAY};
        border-radius: 4px;
        padding: 12px 16px;
        font-family: "SF Mono", Menlo, Consolas, monospace;
        font-size: 9pt;
        line-height: 1.5;
        overflow-wrap: break-word;
        white-space: pre-wrap;
        page-break-inside: avoid;
    }}
    code {{
        font-family: "SF Mono", Menlo, Consolas, monospace;
        font-size: 9pt;
        background: {LIGHT_GRAY};
        padding: 1px 4px;
        border-radius: 2px;
    }}
    pre code {{
        background: none;
        padding: 0;
    }}

    /* ---- Lists ---- */
    ul, ol {{
        margin: 8px 0;
        padding-left: 24px;
    }}
    li {{
        margin: 4px 0;
    }}

    /* ---- Report content wrapper ---- */
    .report-content {{
        /* First h1 in the report body - we hide it since it's on the cover */
    }}
    .report-content > h1:first-child {{
        display: none;
    }}

    /* ---- Header bar on content pages ---- */
    .page-header {{
        display: flex;
        align-items: center;
        padding-bottom: 8px;
        border-bottom: 1px solid {MID_GRAY};
        margin-bottom: 24px;
    }}
    .page-header img {{
        width: 28px;
        height: 28px;
        margin-right: 10px;
    }}
    .page-header-text {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: 12pt;
        font-weight: bold;
        color: {NAVY};
    }}
    .page-header-tagline {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 8pt;
        color: {CYAN};
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-left: 8px;
    }}

    /* Emphasis spans (gold highlight) */
    em {{
        font-style: italic;
    }}
    '''


def postprocess_html(html):
    """Post-process the HTML to clean up and enhance."""
    # Remove the cover-duplicate elements from the body:
    # 1. The h2 subtitle "A GMS Investigation..."
    html = re.sub(
        r'<h2[^>]*>A GMS Investigation into Jersey City Board of Education Contract Transparency</h2>',
        '', html
    )
    # 2. The combined "GMS | OCC Research" + "April 2026" paragraph (they're in one <p> tag)
    html = re.sub(
        r'<p><strong>Governance Memory System \(GMS\) \| OCC Research</strong>\s*<strong>April 2026</strong></p>',
        '', html
    )
    # 4. Remove the first <hr> after the title block (decorative separator)
    html = html.replace('<hr />', '<hr>')
    # Remove the first two <hr> tags (title block separators that are now redundant)
    for _ in range(2):
        html = html.replace('<hr>', '', 1)
    return html


def main():
    print("Reading FINDINGS_REPORT.md...")
    md_text = REPORT_MD.read_text(encoding='utf-8')

    print("Extracting headings for TOC...")
    headings = extract_headings(md_text)

    print("Converting markdown to HTML...")
    body_html = convert_md_to_html(md_text)
    body_html = postprocess_html(body_html)

    print("Building cover page...")
    cover_html = build_cover_page()

    print("Building table of contents...")
    toc_html = build_toc(headings)

    print("Assembling full document...")
    header_bar = f'''
    <div class="page-header">
        <img src="{LOGO_DATA_URI}" alt="OCC Research">
        <span class="page-header-text">OCC Research</span>
        <span class="page-header-tagline">Governance Memory System</span>
    </div>
    '''

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <style>{build_css()}</style>
</head>
<body>
    {cover_html}
    {toc_html}
    {header_bar}
    <div class="report-content">
        {body_html}
    </div>
</body>
</html>
    '''

    # Ensure output directory exists
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating PDF at {OUTPUT_PDF}...")
    HTML(string=full_html, base_url=str(REPORT_MD.parent)).write_pdf(str(OUTPUT_PDF))

    size_mb = OUTPUT_PDF.stat().st_size / (1024 * 1024)
    print(f"Done. PDF saved to {OUTPUT_PDF} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
