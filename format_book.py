import os
import mistune
import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
import mistune
import json
from ebooklib import epub
from bs4 import BeautifulSoup
from slugify import slugify

def read_json_file(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def read_text_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info.strip(), stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)
        # border line.
        return '<div style="border: 1px solid #eaecef; border-radius: 3px; padding: 16px; background-color: #f6f8fa;"><pre><code>%s</code></pre></div>' % mistune.escape(code)

def read_book_data(book_folder):
    book_info = read_json_file(os.path.join(book_folder, "book_info.json"))
    title = book_info["book_title"]
    summary = read_text_file(os.path.join(book_folder, "summary.txt"))

    chapters_data = []
    chapters_outline_file = os.path.join(book_folder, "chapters.json")
    chapters = read_json_file(chapters_outline_file)["chapters"]

    chapters_folder = os.path.join(book_folder, "chapters")
    for chapter in chapters:
        chapter_path = os.path.join(chapters_folder, chapter["title"])
        chapter_outline = read_json_file(os.path.join(chapter_path, "outline.json"))

        sub_chapters = []
        for sub_chapter_info in chapter_outline["sub_chapters"]:
            sub_chapter_title = sub_chapter_info["title"]
            sub_chapter_file = os.path.join(chapter_path, f"{sub_chapter_title}.txt")
            
            if os.path.isfile(sub_chapter_file):
                sub_chapter_data = read_text_file(sub_chapter_file)
                sub_chapters.append({"title": sub_chapter_title, "content": sub_chapter_data})

        chapters_data.append({"title": chapter_outline["chapter_title"], "sub_chapters": sub_chapters})

    return title, summary, chapters_data

def create_ebook_from_folder(book_folder, output_dir, name):
    title, summary, chapters_data = read_book_data(book_folder)

    # Create an EPUB book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier("name")
    book.set_title(title)
    book.set_language("en")
    book.add_author("Sandhaug Digital")
    

    book.add_item(epub.EpubNcx())


    # Read and add the cover image
    cover_image_path = os.path.join(book_folder, "cover.png")  # Assuming the cover image is named 'cover.png'
    if os.path.isfile(cover_image_path):
        with open(cover_image_path, "rb") as img:
            cover_image = epub.EpubImage()
            cover_image.file_name = "cover.png"
            cover_image.media_type = "image/png"
            cover_image.content = img.read()
            book.add_item(cover_image)
            book.set_unique_metadata("OPF", "meta", None, {"name": "cover", "content": cover_image.id})  # Add cover image metadata




        # Generate table of contents
    toc_items = []
    book_chapters = []

    for chapter_data in chapters_data:
        chapter_title = chapter_data["title"]
        chapter = epub.EpubHtml(title=chapter_title, file_name=f"{slugify(chapter_title)}.xhtml", lang="en")
        chapter.content = f"<h1>{chapter_title}</h1>"

        # List to store subchapter items for table of contents
        subchapter_items = []

        for sub_chapter in chapter_data["sub_chapters"]:
            sub_chapter_title = sub_chapter["title"]
            sub_chapter_content = sub_chapter["content"]

            markdown = mistune.create_markdown(renderer=HighlightRenderer())
            html_content = markdown(sub_chapter_content)

            chapter.content += html_content

            # Create a subchapter item and add it to the subchapter_items list
            subchapter_item = epub.Link(chapter.file_name, sub_chapter_title, f"{slugify(chapter_title)}_{slugify(sub_chapter_title)}")
            subchapter_items.append(subchapter_item)

        book.add_item(chapter)

        # Append chapter and its subchapters to the table of contents
        toc_items.append((chapter, subchapter_items))
        book_chapters.append(chapter)

    # Create a navigation file
    nav = epub.EpubNav(uid="nav", file_name="nav.xhtml")
    book.add_item(nav)

    # Define the sequence of the book content
    book.toc = [epub.Section('Table of Contents')] + toc_items


    # Add the chapters to the book spine
    book.spine = ["nav"] + book_chapters

    # Create an EPUB file
    epub.write_epub(os.path.join(output_dir, f"{name}.epub"), book)


def main(name):
    # Use the function to create an ebook from the folder structure
    book_folder = f"books/{name}"
    output_dir = book_folder
    create_ebook_from_folder(book_folder, output_dir, name)
    print("Done", "Saved to", f"{output_dir}/{name}.epub")

    # execute java -jar epubcheck-5.0.0/epubcheck.jar books/python_oop_intro_7543d8df-7955-49fd-b04a-00c04c338fa8/Introduction\ to\ Object-Oriented\ Programming\ in\ Python.epub
    os.system(f"java -jar epubcheck-5.0.0/epubcheck.jar books/{name}/{name}.epub")

if __name__ == "__main__":
    main("self_care_ebook_6c8c363c-5d47-428d-9701-8897bbe1ae94")

