import time
import re
import openai
import os
from docx import Document
from tqdm import tqdm
import concurrent.futures
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import random

total_price = 0
counter = 1

def chat(messages):
    global total_price, counter
    model = "gpt-4"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # c = counter
    # counter += 1
    # # sleep random time between 0.5 and 1.5 seconds
    # time.sleep(0.5 + 1 * random.random())
    # return str(c)

    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages
            )


            completion_tokens = response["usage"]["completion_tokens"]
            prompt_tokens = response["usage"]["prompt_tokens"]

            #$0.002 / 1K tokens
            if model == "gpt-3.5-turbo":
                price = completion_tokens * 0.000002 + prompt_tokens * 0.000002
            else :
                price = completion_tokens * 0.00006 + prompt_tokens * 0.00003
            # print("Price: ", price)
            total_price += price
            # Print with green colors.
            print("\033[92m" + "Price: " + str(price) +"\tTotal price: "+str(total_price)+ "\033[0m")


            content = response['choices'][0]['message']['content']
            return content
        except openai.error.RateLimitError:
            # TODO: WHen we switch to langchain, this is built in
            print("Error: ", "API Rate Limit Reached. Waiting 10 seconds...")
            time.sleep(10)




def split_text_into_paragraphs(text):
    return [paragraph.strip() for paragraph in re.split(r'\n\n+', text)]

def correct_text_paragraph(text_paragraph):
    initial_system_prompt = {
    "role": "system",
    "content": "You are WriterAI, a writing assistant. Correct the text paragraph from a bachelor thesis for grammar, spelling, and structure. Provide comments on improvements and corrected versions of specific parts needing change, not the full paragraph (e.g for 'eggs bread and bacon' respond with 'eggs, bread' so the user understands the correction). If it's a headline or non-text, Or if the content is sufficiently good and correct, reply 'lgtm'.\n\nTarget audience: Our report targets educators, evaluators, and students interested in the development and implementation of a data platform manager. It's a comprehensive and informative resource covering relevant information, development processes, and insights."
    }
    user_message = {
        "role": "user",
        "content": text_paragraph
    }
    messages = [initial_system_prompt, user_message]
    return chat(messages)

def process_text_file(file_path):
    with open(file_path, 'r') as f:
        text = f.read()

    paragraphs = split_text_into_paragraphs(text)
    corrections = []

    for paragraph in paragraphs:
        if paragraph:
            correction = correct_text_paragraph(paragraph)
            corrections.append(correction)

    return paragraphs, corrections

def generate_html_file(original_chunks, corrected_chunks, output_html_path):
    with open(output_html_path, 'w') as f:
        f.write("""
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0 auto; max-width: 1200px; }
                    table { width: 100%; table-layout: fixed; border-collapse: collapse; }
                    th, td { padding: 10px; vertical-align: top; word-wrap: break-word; border: 1px solid #ddd; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    .correction { background-color: yellow; }
                    h1, h2 { padding-top: 50px; margin-bottom: 0; }
                    .chapter { page-break-before: always; }
                    .content { white-space: pre-wrap; word-wrap: break-word; font-family: Arial, sans-serif; margin: 0; }
                </style>
            </head>
            <body>
        """)

        f.write("<table>")
        f.write("<tr><th>Original Chunk</th><th>Corrected Chunk</th></tr>")
        for original, corrected in zip(original_chunks, corrected_chunks):
            if original.strip() and corrected.strip():
                f.write(f"""
                    <tr>
                        <td><div class='content'>{original}</div></td>
                        <td class='correction'><div class='content'>{corrected}</div></td>
                    </tr>
                """)

        f.write("</table>")
        f.write("</body></html>")


def is_chapter_title(paragraph):
    return paragraph.style.name == "Heading 1"

def is_subchapter_title(paragraph):
    return paragraph.style.name == "Heading 2"

def is_sub_subchapter_title(paragraph):
    return paragraph.style.name == "Heading 3"



def split_content_into_chunks(content, max_words=2000):
    chunks = []
    current_chunk = []
    current_word_count = 0

    paragraphs = content.split('\n\n')  # Split the content into paragraphs

    for paragraph in paragraphs:
        paragraph_word_count = len(paragraph.split())
        if current_word_count + paragraph_word_count <= max_words:
            current_chunk.append(paragraph)
            current_word_count += paragraph_word_count
        else:
            print("Chunking paragraph", paragraph[:100])
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_word_count = paragraph_word_count

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks



def extract_chapters_and_subchapters(doc):
    chapters = []

    current_chapter = None
    current_sub_chapter = None
    current_sub_sub_chapter = None

    for paragraph in doc.paragraphs:
        paragraph_text = paragraph.text.strip()
        if is_chapter_title(paragraph):
            if current_chapter:
                if current_sub_chapter:
                    if current_sub_sub_chapter:
                        current_sub_chapter["subsubchapters"].append(current_sub_sub_chapter)

                    current_chapter["subchapters"].append(current_sub_chapter)

                chapters.append(current_chapter)

            current_chapter = {"title": paragraph_text, "subchapters": [], "content": ""}
            current_sub_chapter = None
            current_sub_sub_chapter = None
        elif is_subchapter_title(paragraph):
            if current_sub_chapter:
                if current_sub_sub_chapter:
                    current_sub_chapter["subsubchapters"].append(current_sub_sub_chapter)

                current_chapter["subchapters"].append(current_sub_chapter)
            current_sub_chapter = {"title": paragraph_text, "subsubchapters": [], "content": ""}
            current_sub_sub_chapter = None
            
        elif is_sub_subchapter_title(paragraph):
            if current_sub_sub_chapter:
                current_sub_chapter["subsubchapters"].append(current_sub_sub_chapter)
            current_sub_sub_chapter = {"title": paragraph_text, "content": ""}
        else:
            if current_sub_sub_chapter:
                current_sub_sub_chapter["content"] += "\n\n" + paragraph_text
            elif current_sub_chapter:
                current_sub_chapter["content"] += "\n\n" + paragraph_text
            elif current_chapter:
                current_chapter["content"] += "\n\n" + paragraph_text

    if current_sub_sub_chapter:
        current_sub_chapter["subsubchapters"].append(current_sub_sub_chapter)

    if current_sub_chapter:
        current_chapter["subchapters"].append(current_sub_chapter)

    if current_chapter:
        chapters.append(current_chapter)

    return chapters

def process_docx_file(file_path):
    doc = Document(file_path)
    chapters = extract_chapters_and_subchapters(doc)

    all_chunks = []
    for chapter in chapters:
        # print(chapter)
        if chapter.get("content", "").strip():
            chunks = split_content_into_chunks(chapter["title"] + chapter["content"])
            all_chunks.extend(chunks)
        for sub_chapter in chapter["subchapters"]:
            if sub_chapter.get("content", "").strip():
                chunk = sub_chapter["title"] + sub_chapter["content"]
            else:
                chunk = sub_chapter["title"]
            for sub_sub_chapter in sub_chapter["subsubchapters"]:
                if sub_sub_chapter["content"].strip():
                    chunk += "\n\n" + sub_sub_chapter["title"] + "\n\n" + sub_sub_chapter["content"]

            chunks = split_content_into_chunks(chunk)
            all_chunks.extend(chunks)


    corrections_dict = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk_index = {executor.submit(correct_text_paragraph, chunk): i for i, chunk in enumerate(all_chunks)}

        for future in tqdm(concurrent.futures.as_completed(future_to_chunk_index), total=len(all_chunks), desc="Processing chunks", ncols=100):
            chunk_index = future_to_chunk_index[future]
            try:
                correction = future.result()
            except Exception as e:
                print(f"Error occurred while processing chunk with index {chunk_index}: {e}")
                correction = ""
            corrections_dict[chunk_index] = correction

    # Create a list of tuples containing the original chunk and its corresponding correction
    ordered_corrections = [corrections_dict[i] for i in range(len(all_chunks))]
    original_and_corrected = list(zip(all_chunks, ordered_corrections))

    # Sort the list based on the index of the original chunk in the all_chunks list
    original_and_corrected.sort(key=lambda x: all_chunks.index(x[0]))

    # Unpack the sorted list into two separate lists
    original_chunks, corrections = zip(*original_and_corrected)

    return original_chunks, corrections


if __name__ == "__main__":
    input_file_path = "input.docx"
    output_file_path = "output.txt"
    output_html_path = "output.html"

    original_chunks, corrections = process_docx_file(input_file_path)

    with open(output_file_path, 'w') as f:
        f.write("\n\n".join(corrections))

    generate_html_file(original_chunks, corrections, output_html_path)
