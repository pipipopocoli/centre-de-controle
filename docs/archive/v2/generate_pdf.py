import sys
import os
from playwright.sync_api import sync_playwright

# Configuration
MD_FILE = "docs/cockpit_v2_whitepaper.md"
PDF_FILE = "docs/cockpit_v2_whitepaper.pdf"
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cockpit V2 Whitepaper</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
    <style>
        body { 
            box-sizing: border-box; 
            min-width: 200px; 
            max-width: 980px; 
            margin: 0 auto; 
            padding: 45px; 
            font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
        }
        .markdown-body { box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }
        @media print {
            body { padding: 0; }
            .markdown-body { padding: 0; }
        }
        .mermaid { display: flex; justify-content: center; margin: 2em 0; }
    </style>
</head>
<body class="markdown-body">
    <div id="content"></div>
    <script>
        const mdContent = `__MD_CONTENT_PLACEHOLDER__`;
        
        // Custom renderer to handle mermaid blocks
        document.getElementById('content').innerHTML = marked.parse(mdContent);
        
        // Transform mermaid code blocks to divs
        document.querySelectorAll('pre code.language-mermaid').forEach(block => {
            const graphDefinition = block.textContent;
            const newDiv = document.createElement('div');
            newDiv.className = 'mermaid';
            newDiv.textContent = graphDefinition;
            block.parentNode.replaceWith(newDiv);
        });

        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>
"""

def generate_pdf():
    # 1. Read Markdown
    if not os.path.exists(MD_FILE):
        print(f"Error: {MD_FILE} not found.")
        sys.exit(1)
        
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Escape backticks and dollars for JS template string
    js_safe_content = md_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    
    # 2. Inject into HTML
    html_content = HTML_TEMPLATE.replace("__MD_CONTENT_PLACEHOLDER__", js_safe_content)
    
    # Save temp HTML for debugging
    with open("docs/temp_render.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. Render with Playwright
    print("Launching Playwright (System Chrome)...")
    with sync_playwright() as p:
        try:
            # Point to the system Chrome we found
            browser = p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        except Exception as e:
            print(f"Failed to launch system chrome: {e}")
            sys.exit(1)
                
        page = browser.new_page()
        
        # Load the HTML content directly
        # We use set_content instead of goto file:// to avoid path issues
        page.set_content(html_content, wait_until="networkidle")
        
        # Wait specifically for mermaid diagrams to be rendered
        # Mermaid adds data-processed attribute or changes generated SVG
        page.wait_for_timeout(2000) # Give mermaid 2 seconds to render (simple heuristic)
        
        print(f"Generating PDF to {PDF_FILE}...")
        page.pdf(path=PDF_FILE, format="A4", print_background=True, margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"})
        
        browser.close()
        print("Done!")

if __name__ == "__main__":
    generate_pdf()
