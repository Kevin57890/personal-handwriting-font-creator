from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path


class FontSampleExporter:
    def export_html(
        self,
        output_path: Path,
        font_path: Path,
        family_name: str,
        sample_text: str,
        saved_count: int,
        total_count: int,
    ) -> Path:
        output_path = Path(output_path)
        font_path = Path(font_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        relative_font = font_path.name if font_path.parent == output_path.parent else font_path.as_posix()
        body_text = sample_text.strip() or "Hello World!"
        glyph_line = "ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789\n.,!?;:'\"()[]{}-_/\\@#&$%+*=<>"

        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(family_name)} Font Sample</title>
  <style>
    @font-face {{
      font-family: "{escape(family_name)}";
      src: url("{escape(relative_font)}") format("truetype");
    }}
    :root {{
      color-scheme: light;
      --ink: #101827;
      --muted: #617084;
      --paper: #ffffff;
      --line: #d7dee8;
      --accent: #1d9a8a;
      --gold: #f2b84b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: #edf2f7;
      color: var(--ink);
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1120px, calc(100vw - 48px));
      margin: 42px auto;
    }}
    header {{
      background: #101827;
      color: white;
      border-radius: 18px;
      padding: 34px 38px;
    }}
    h1 {{
      margin: 0;
      font-size: 36px;
      letter-spacing: 0;
    }}
    .meta {{
      color: #c8d3e2;
      margin-top: 10px;
      font-size: 15px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.35fr 0.65fr;
      gap: 18px;
      margin-top: 18px;
    }}
    section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 26px;
    }}
    .sample {{
      font-family: "{escape(family_name)}", cursive;
      font-size: clamp(46px, 7vw, 88px);
      line-height: 1.18;
      margin: 18px 0 0;
    }}
    .glyphs {{
      white-space: pre-wrap;
      font-family: "{escape(family_name)}", cursive;
      font-size: 38px;
      line-height: 1.45;
      margin: 16px 0 0;
    }}
    h2 {{
      margin: 0;
      font-size: 17px;
    }}
    .stat {{
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
      padding: 14px 0;
      color: var(--muted);
    }}
    .stat strong {{ color: var(--ink); }}
    .bar {{
      height: 10px;
      background: #e2e8f0;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 18px;
    }}
    .bar span {{
      display: block;
      height: 100%;
      width: {round(saved_count / max(total_count, 1) * 100, 2)}%;
      background: linear-gradient(90deg, var(--accent), var(--gold));
    }}
    footer {{
      color: var(--muted);
      margin-top: 18px;
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      .grid {{ grid-template-columns: 1fr; }}
      main {{ width: min(100vw - 28px, 1120px); margin: 20px auto; }}
      header {{ padding: 26px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{escape(family_name)}</h1>
      <div class="meta">Installable handwriting font sample - generated {escape(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))}</div>
    </header>
    <div class="grid">
      <section>
        <h2>Preview Text</h2>
        <p class="sample">{escape(body_text)}</p>
      </section>
      <section>
        <h2>Coverage</h2>
        <div class="stat"><span>Saved glyphs</span><strong>{saved_count}/{total_count}</strong></div>
        <div class="stat"><span>Font file</span><strong>{escape(font_path.name)}</strong></div>
        <div class="bar"><span></span></div>
      </section>
    </div>
    <section style="margin-top: 18px;">
      <h2>Character Sheet</h2>
      <div class="glyphs">{escape(glyph_line)}</div>
    </section>
    <footer>Open this file in a browser after generating the TTF. The page uses the exported font through @font-face.</footer>
  </main>
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")
        return output_path

