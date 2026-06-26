import markdown as md_lib

class DocumentService:
    def __init__(self):
        self.md_extensions = ['tables', 'fenced_code', 'toc']

    def render_html(self, md_content: str, title: str = "Document", branding: dict = None) -> str:
        html_body = md_lib.markdown(md_content, extensions=self.md_extensions)
        colors = branding or {}
        pk = colors.get("primary_color", "#1a365d")
        sk = colors.get("secondary_color", "#2c5282")
        logo = ""
        if colors.get("logo_url"):
            logo = f"<img src='{colors['logo_url']}' style='max-height:60px;margin-bottom:20px'/>"
        return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>{title}</title>
<style>
@page{{size:A4;margin:2cm}}
body{{font-family:Segoe UI,Helvetica,Arial,sans-serif;line-height:1.6;color:#2d3748;margin:0;padding:40px 20px}}
.container{{max-width:900px;margin:0 auto;background:white;padding:60px;box-shadow:0 4px 6px rgba(0,0,0,.1);border-radius:8px}}
h1{{color:{pk};border-bottom:3px solid {pk};padding-bottom:10px}}
h2{{color:{sk};border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin-top:2em}}
table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:.95em}}
th{{background-color:{pk};color:white;text-align:left;padding:12px}}
td{{border-bottom:1px solid #e2e8f0;padding:10px 12px}}
tr:nth-child(even){{background:#f8f9fa}}
@media print{{body{{background:white;padding:0}}.container{{box-shadow:none;max-width:100%;padding:20px}}}}
</style></head>
<body><div class="container">{logo}{html_body}</div></body></html>"""

doc_service = DocumentService()