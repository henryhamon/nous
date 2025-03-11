import uuid
from datetime import datetime
# QuickReader shall aggregate summaries generated within Notion and synthesize them into an EPUB format, facilitating reading on Kindle devices.

class QuickReader:
    TOC_TEMPLATE = """
    <nav epub:type="toc" id="toc" role="doc-toc">
        <h1>Table of Contents</h1>
        <ol style="padding-left: 0;">
            {toc_items}
        </ol>
    </nav>
    """

    TOC_ITEM_TEMPLATE = """
    <li style="list-style-type: none; text-indent: 0; margin-top: 1em;">
    <a href="story{index}.html">{title}</a>
    </li>
    """

    DOC_TEMPLATE = """
    <?xml version='1.0' encoding='utf-8'?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/#" lang="en" xml:lang="en">
    <head/>
    <body><h4>{title}</h4>
        {content}
    </body>
    </html>
    """

    ARTICLE_TEMPLATE = """
        <article>
            <h1>{title}</h1>
            <hr/>
            <p>
                {description}
            </p>
            <ul>
                <li>
                    <span>{created_at}</span>
                </li>
                <li>
                    <a href="{url}">Go to Original</a>
                </li>
            </ul>
            <div>{content}</div>
            <p>{tags}</p>
            <hr/>
        </article>
    """

    def __init__(self, notion):
        self.notion = notion
        self.toc_items = []
        self.epub = None

    def generate_unique_id(self):
        """Generate a unique identifier for the epub book"""
        return str(uuid.uuid4())

    def check_ebooklib_installation(self):
        try:
            import ebooklib
            return True
        except ImportError:
            print("Warning: 'ebooklib' package is not installed!")
            user_input = input("Would you like to install ebooklib now? (y/n): ")
            
            if user_input.lower() == 'y':
                try:
                    import subprocess
                    import sys
                    
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "ebooklib"])
                    print("Successfully installed ebooklib!")
                    return True
                except Exception as e:
                    print(f"Failed to install ebooklib: {str(e)}")
                    print("Please install it manually using: pip install ebooklib")
                    return False
            else:
                print("Please install ebooklib manually using: pip install ebooklib")
                return False

    def __init__(self):
        if (not self.check_ebooklib_installation()):
            # Handle the case where ebooklib is not available
            print("Cannot proceed without ebooklib installation")

    def digest(self, news = []):
        if (self.check_ebooklib_installation()):
            from ebooklib import epub
        else:
            # Handle the case where ebooklib is not available
            print("Cannot proceed without ebooklib installation")
            return

        self.toc_items = []
        self.epub = epub.EpubBook()
        self.epub.set_identifier(self.generate_unique_id())
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.epub.set_title(f"{len(news)} news summarized articles  {current_date}")
        self.epub.set_language('en')

        chapter_id = -1
        for chapter in news:
            chapter_id += 1
            chapter_title = chapter["title"]

            chapter_html = self.ARTICLE_TEMPLATE.format(
                title=chapter_title,
                content=chapter["abstract"],
                description=chapter["description"],
                tags=chapter["tag"],
                created_at=chapter["date"],
                url=chapter["url"]
            )

            epub_chapter = epub.EpubHtml(title=chapter_title, file_name=f"story{chapter_id}.html", lang='en')
            epub_chapter.content = chapter_html
            self.epub.add_item(epub_chapter)

            self.toc_items.append(self.TOC_ITEM_TEMPLATE.format(
                index=chapter_id,
                title=chapter_title,
            ))
        epub_toc = epub.EpubNav()
        epub_toc.title = "Table of Contents"
        epub_toc.toc = self.toc_items
        self.epub.add_item(epub_toc)

        self.book = epub.write_epub(f"quickreader_{current_date}.epub", self.epub, {})