import time
import re
import openai
import os
from docx import Document

total_price = 0


def chat(messages):
    global total_price
    model = "gpt-3.5-turbo"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # return "test123"

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
    "content": "You are WriterAI, a writing assistant. Correct the text paragraph from a bachelor thesis for grammar, spelling, and structure. Provide comments on improvements and corrected versions of specific parts needing change, not the full paragraph. If it's a headline or non-text, reply 'lgtm'.\n\nTarget audience: Our report targets educators, evaluators, and students interested in the development and implementation of a data platform manager. It's a comprehensive and informative resource covering relevant information, development processes, and insights."
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

def generate_html_file(original_paragraphs, corrected_paragraphs, output_html_path):
    with open(output_html_path, 'w') as f:
        f.write("<html><head><style>body { font-family: Arial, sans-serif; } table { width: 100%; table-layout: fixed; } td { vertical-align: top; width: 50%; word-wrap: break-word; } .correction { background-color: yellow; }</style></head><body><table>")
        for original, corrected in zip(original_paragraphs, corrected_paragraphs):
            f.write(f"<tr><td>{original}</td><td class='correction'>{corrected}</td></tr>")
        f.write("</table></body></html>")


import concurrent.futures

# ...

def process_docx_file(file_path):
    doc = Document(file_path)
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()]

    corrections = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_paragraph = {executor.submit(correct_text_paragraph, paragraph): paragraph for paragraph in paragraphs}
        for future in concurrent.futures.as_completed(future_to_paragraph):
            paragraph = future_to_paragraph[future]
            try:
                correction = future.result()
            except Exception as e:
                print(f"Error occurred while processing paragraph '{paragraph}': {e}")
                correction = ""
            corrections.append(correction)

    # Reorder corrections to match the original order of paragraphs
    ordered_corrections = [correction for _, correction in sorted(zip(paragraphs, corrections), key=lambda pair: pair[0])]

    return paragraphs, ordered_corrections


if __name__ == "__main__":
    input_file_path = "input.docx"  # Change the file extension to .docx
    output_file_path = "output.txt"
    output_html_path = "output.html"

    original_paragraphs, corrections = process_docx_file(input_file_path)

    with open(output_file_path, 'w') as f:
        f.write("\n\n".join(corrections))

    generate_html_file(original_paragraphs, corrections, output_html_path)
