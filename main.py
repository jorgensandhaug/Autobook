import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from chat import chat, chat_json_response
import os
import uuid

continous_mode = False
folder_name = None
# Helper function to save JSON data to file
def save_to_file(folder_name, file_name, data):
    os.makedirs(folder_name, exist_ok=True)
    with open(f"{folder_name}/{file_name}.json", "w") as f:
        json.dump(data, f, indent=2)

    pretty_print("Saved to file: ", f"{folder_name}/{file_name}.json")

def save_to_file_text(folder_name, file_name, data):
    os.makedirs(folder_name, exist_ok=True)
    with open(f"{folder_name}/{file_name}.txt", "w") as f:
        f.write(data)

    pretty_print("Saved to file: ", f"{folder_name}/{file_name}.txt")

def get_user_feedback(prompt):
    global continous_mode
    if continous_mode:
        return "yes"
    # stylize prompt with colors (green)
    return input("\033[92m" + prompt + "\033[0m")

def pretty_print(title, json_or_string):
    # with colors
    print("\033[1m" + title + "\033[0m")
    if isinstance(json_or_string, str):
        print(json_or_string)
    else:
        print(json.dumps(json_or_string, indent=4))

def get_book_info(book_idea):
    book_info = None
    initial_system_prompt = {
        "role": "system",
        "content": (
            "You are an AI book assistant. Please help the user by expanding on their book idea, "
            "identify the target audience, and provide general instructions about the book. In the book_instructions, "
            "mention that the author has personal experience in the subject, but state that this should *not* be mentioned explicitly "
            "and also that the author should not be talked about at all in the book. The writing style, tone and additional instructions will optionally be specified "
            "in the book idea, but if it's not present, try to come up with it anyways. You have to give us an instruction that no external resources can be mentioned or referred to explicitly in the book. In your response, provide a JSON object containing the book_title and book_instructions as well as title_folder_name (super short folder name just for file handling purposes)."
            "Format your response as: ```json\n<json response>\n```"
        ),
    }
    book_idea_message = {
        "role": "user",
        "content": book_idea,
    }
    messages = [initial_system_prompt, book_idea_message]

    while not book_info:
        book_info = chat_json_response(messages)
        pretty_print("Book info: ", book_info)
        messages.append({"role": "assistant", "content": json.dumps(book_info, indent=4)})
        user_feedback = get_user_feedback("Do you accept the book info (Y/no)? If no, please provide your suggestions: ")
        if user_feedback.lower() != "yes" and user_feedback.lower() != "":
            messages.append({"role": "user", "content": user_feedback})
            book_info = None
        else:
            return book_info



def generate_book_outline(book_instructions):
    full_outline = None
    system_prompt = {
        "role": "system",
        "content": "Based on the book info provided, generate a detailed outline for the entire book, including a brief description of each chapter. This outline will be used to create more detailed information for each chapter later. and give your response in JSON using the following format: {'chapters': [{'title': 'Chapter 1', 'main_content_outline': 'This is the main content outline for chapter 1, with brief information about the content and the structure.', 'sub_chapters': ['sub_chapter_title_1', ...]}, ...]}. Format your response as: ```json\n<json response>\n```",
    }
    book_instructions_message = {
        "role": "user",
        "content": "Book info: " + book_instructions,
    }
    messages = [system_prompt, book_instructions_message]
    while not full_outline:
        full_outline = chat_json_response(messages)
        pretty_print("Full outline: ", json.dumps(full_outline, indent=4))
        messages.append({"role": "assistant", "content": json.dumps(full_outline, indent=4)})
        user_feedback = get_user_feedback("Do you accept the full outline (Y/no)? If no, please provide your suggestions: ")
        if user_feedback.lower() != "yes" and user_feedback.lower() != "":
            messages.append({"role": "user", "content": user_feedback})
            full_outline = None
        else:
            save_to_file(f"books/{folder_name}", "full_outline", full_outline)
            return full_outline





def get_all_chapters(book_instructions, full_outline):
    res = None
    # Include the full outline in the chapters_system_prompt
    chapters_system_prompt = {
        "role": "system",
        "content":
    (
        "Generate a json response containing an array of chapters with fields "
        "title(string), main_content_outline (string), and instructions (string), "
        "for each chapter, based on the general information about the book, the "
        "full outline provided, and considering the target audience. Make sure each "
        "chapter is coherent and connected, avoiding redundancy and maintaining "
        "consistency throughout the book. When later creating the chapters one by "
        "one, the information provided in your response for each chapter should alone "
        "be sufficient to achieve this Consistency and Redundancy. In the instructions "
        "make sure to include, for example, specifics about what the chapter should not include (for example if something is relevant, but it is better to go into depth in one of the other chapters), and also any additional "
        "instructions you find reasonable, as well as something about the length or "
        "the depth of that chapter. format your response in the following way:\n"
        "```json\n<json response>\n```\n"
    )
    }

    full_outline_message = {
        "role": "user",
        "content": "Full outline: " + json.dumps(full_outline, indent=4) + "\n" + "Book info: " + book_instructions,

    }
    messages = [chapters_system_prompt, full_outline_message]
    while not res:
        res = chat_json_response(messages)
        pretty_print("Chapters: ", res)
        messages.append({"role": "assistant", "content": json.dumps(res, indent=4)})
        user_feedback = get_user_feedback("Do you accept the chapters (Y/no)? If no, please provide your suggestions: ")
        if user_feedback.lower() != "yes" and user_feedback.lower() != "":
            messages.append({"role": "user", "content": user_feedback + "\nStill only provide the chapters in the same format as before"})
            res = None
        else:
            save_to_file(f"books/{folder_name}", "chapters", res)
            return res["chapters"]
        

def get_summary(book_instructions, chapters):
    summary = None
    summary_prompt = {
        "role": "system",
        "content": (
            "Generate an extensive summary of the books content, considering the book info and the provided chapters. "
            "The summary should give a clear idea of what the book is about and its main takeaways. "
            "In your response, only provide the text for the summary"
        ),
    }
    book_and_chapters_message = {
        "role": "user",
        "content": json.dumps({"book_instructions": book_instructions, "chapters": chapters}),
    }
    messages = [summary_prompt, book_and_chapters_message]
    while not summary:
        summary = chat(messages)
        pretty_print("Summary: ", summary)
        messages.append({"role": "assistant", "content": summary})
        user_feedback = get_user_feedback("Do you accept the summary (Y/no)? If no, please provide your suggestions: ")
        if user_feedback.lower() != "yes" and user_feedback.lower() != "":
            messages.append({"role": "user", "content": user_feedback + "\nStill only provide the summary in your response."})
            summary = None
        else:
            save_to_file_text(f"books/{folder_name}", "summary", summary)
            return summary



def expand_chapter_outline(chapter, full_outline, summary, book_instructions):
    chapter_outline = None
    system_prompt = {
    "role": "system",
    "content": (
        "Generate a more detailed outline for the given chapter, dividing it into "
        "sub-chapters, considering the summary, the full book outline, and book_instructions provided. Make "
        "sure the sub-chapters are coherent, connected, and follow the main "
        "content outline and instructions provided for the chapter. Ensure the outline maintains "
        "logical flow and smooth transitions between sub-chapters. "
        "In the instructions, make sure to include, for example, specifics about what the sub-chapter should not include "
        "(for example if something is relevant, but it is better to go into depth in one of the other sub-chapters), and also any additional "
        "instructions you find reasonable, as well as something about the length or the depth of that sub-chapter. For all decisions that have to be made in any of the sub-chapters, you have to make these decisions now and make sure they are included in the instructions of all the relevant sub-chapters. This is necessary for all of the sub-chapters to be cohesive and in agreement, since they are later to be written by different people who will only have access to the specific sub-chapter info, book summary and chapter main outline. Also, provide a brief summary of the connections "
        "between the sub-chapters and how they relate to the overall chapter theme.\n\n"
        "Before the JSON response, give a textual response where you think and reason about what kinds of decisions have to be made, as well as the brief summary and other important things to remember to put in the instructions.\n\n"
        "Format the response as first the thought process and connections, then a JSON object containing the following fields:\n"
        "{\n"
        "  'chapter_title': 'The title of the chapter (string)',\n"
        "  'sub_chapters': [\n"
        "    {\n"
        "      'title': 'The title of the sub-chapter (string)',\n"
        "      'outline': 'A brief description of the sub-chapter's content (string)',\n"
        "      'instructions': 'Any specific instructions for writing the sub-chapter (string) (be detailed and exhaustive in the instructions)',\n"
        "      'index': 'The index of the sub-chapter in the chapter starting from 1 (integer: 1, 2, 3...)',\n"
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Give your answer in the following way:\n"
        "Thought process: <text>\n\n"
        "```json\n"
        "<json response>\n"
        "```\n"
        ),
    }

    chapter_message = {
        "role": "user",
        "content": json.dumps(
            {
                "chapter": chapter,
                "full_outline": full_outline,
                "summary": summary,
                "book_instructions": book_instructions,
            }
        ),
    }
    messages = [system_prompt, chapter_message]
    while not chapter_outline:
        chapter_outline = chat_json_response(messages)
        try: 
            print("Outline for chapter: ", chapter_outline["chapter_title"])
            pretty_print("Chapter outline: ", chapter_outline)
            messages.append({"role": "assistant", "content": json.dumps(chapter_outline, indent=4)})
            user_feedback = get_user_feedback("Do you accept the chapter outline (Y/no)? If no, please provide your suggestions: ")
            if user_feedback.lower() != "yes" and user_feedback.lower() != "":
                messages.append({"role": "user", "content": user_feedback + "\nStill only provide the chapter outline in your response in the correct format."})
                chapter_outline = None
            else:
                save_to_file(f"books/{folder_name}/chapters/{chapter_outline['chapter_title']}", "outline", chapter_outline)
                return chapter_outline
        except:
            # warn with yellow
            print("\033[93m" + "Error: chapter outline not json. Giving another chance to write the chapter outline." + "\033[0m")
            messages.append({"role": "assistant", "content": chapter_outline[1]})
            messages.append({"role": "user", "content": "You did not provide your response in the correct JSON format. See the error message below:\n"+chapter_outline[0]+"\nOnly provide the chapter outline in your response in the correct json format."})
            chapter_outline = None 






# Modify write_sub_chapter function to accept chapter_main_outline
def write_sub_chapter(chapter_title, sub_chapter, chapter_main_outline, summary):
    system_prompt = {
        "role": "system",
        "content": (
            "Write the content for the given sub-chapter, following the sub-chapter outline, "
            "instructions provided, the main chapter outline, and the full book summary. Ensure the content "
            "is coherent, connected, and avoids redundancy. The length and depth of "
            "the sub-chapter should be in accordance with the instructions. In your response, only provide the full text for the sub-chapter. Remember that this is an e-book, so don't write too long paragraphs. Provide your response in Markdown format!"
        ),
    }
    sub_chapter_message = {
        "role": "user",
        "content": json.dumps({"sub_chapter": sub_chapter, "chapter_main_outline": chapter_main_outline, "summary": summary}),
    }
    messages = [system_prompt, sub_chapter_message]
    sub_chapter_content = chat(messages)
    save_to_file_text(f"books/{folder_name}/chapters/{chapter_title}", sub_chapter["title"], sub_chapter_content)
    return sub_chapter_content

# Update write_chapter_expanded_outline to pass chapter_main_outline to write_sub_chapter
lock = threading.Lock()
def write_chapter_expanded_outline(chapter, full_outline, summary, book_instructions):
    global lock
    if continous_mode:
        # blue print
        print("\033[94m" + "Expanding chapter: " + chapter['title'] + "\033[0m")
        expanded_outline = expand_chapter_outline(chapter, full_outline, summary, book_instructions)
        sub_chapters = expanded_outline['sub_chapters']
        title = expanded_outline['chapter_title']
        print("Writing chapter: " + title)

        chapter_main_outline = chapter['main_content_outline']

    else:
        with lock:
            # blue print
            print("\033[94m" + "Expanding chapter: " + chapter['title'] + "\033[0m")
            expanded_outline = expand_chapter_outline(chapter, full_outline, summary, book_instructions)
            sub_chapters = expanded_outline['sub_chapters']
            title = expanded_outline['chapter_title']
            print("Writing chapter: " + title)

            chapter_main_outline = chapter['main_content_outline']

    with ThreadPoolExecutor() as executor:
        written_sub_chapters = list(executor.map(lambda sub_chapter: write_sub_chapter(title, sub_chapter, chapter_main_outline, summary), sub_chapters))
    chapter_text = chapter['title'] + "\n\n" + "\n\n".join(written_sub_chapters)
    pretty_print("Finished writing chapter: \n", chapter['title'])

    #save chapter to file in books  folder
    save_to_file_text(f"books/{folder_name}/chapters/{title}", "full_chapter", chapter_text)

    return chapter_text






def main(args):
    global folder_name
    book_idea = "Intro to object oriented programming in python. Make sure to not include any external resources in any place in the book."
    book_info = get_book_info(book_idea)
    book_title = book_info["book_title"]
    title_folder_name = book_info["title_folder_name"]

    book_uuid = uuid.uuid4()
    folder_name = title_folder_name + "_" + str(book_uuid)
    save_to_file(f"books/{folder_name}", "book_info", book_info)

    # Generate a full outline of the book
    full_outline = generate_book_outline(book_info["book_instructions"])

    # Get all chapters
    chapters = get_all_chapters(book_info["book_instructions"], full_outline)

    # Get the summary
    summary = get_summary(book_info["book_instructions"], chapters)


    with ThreadPoolExecutor() as executor:
        written_chapters = list(
            executor.map(
                lambda chapter: write_chapter_expanded_outline(chapter, full_outline, summary, book_info["book_instructions"]),
                chapters,
            )
        )

    # without multithreading.
    # written_chapters = []
    # for chapter in chapters:
    #     written_chapters.append(write_chapter_expanded_outline(chapter, full_outline, summary, book_info["book_instructions"]))


    # Combine written chapters
    book_content = "\n\n".join(written_chapters)

    # Save book to file
    save_to_file_text(f"books/{folder_name}", "full_book", book_content)
    print("Finished writing book: \n\n\n", "Folder name: ", folder_name)
    from chat import total_price
    print("Total price: ", total_price)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--continuous", action="store_true", help="Enable continuous mode")
    args = parser.parse_args()
    
    if args.continuous:
        continous_mode = True
        
    main(args)