from bs4 import BeautifulSoup
import re
import openai
import time
import os
import json

total_price = 0


def chat(messages):
    global total_price
    model = "gpt-4"
    openai.api_key = os.getenv("OPENAI_API_KEY")

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





def chat_json_response(messages):
    # Make sure to use correct JSON structure in your response to the end of the last message content.
    messages[-1]["content"] += "Make sure to use valid JSON structure in your response"
    content = chat(messages)
    try:
        # Try the original regex-based method first
        json_start_pattern = re.compile(r'```json')
        json_start_pattern2 = re.compile(r'```')
        json_end_pattern = re.compile(r'```')

        json_start = json_start_pattern.search(content)
        if json_start is None:
            json_start = json_start_pattern2.search(content)

        json_end = json_end_pattern.search(content, json_start.end())

        json_content = content[json_start.end():json_end.start()]
        json_data = json.loads(json_content.strip())

        return json_data
    except Exception as e1:
        print("Error occurred while extracting JSON content using regex-based method:")
        print(str(e1))

        try:
            # If the original method fails, try the string search method as a fallback
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            json_content = content[json_start:json_end]
            json_data = json.loads(json_content.strip())

            return json_data
        except Exception as e2:
            print("Error occurred while extracting JSON content using string search method:")
            print(str(e2))
            print("\nUnable to extract JSON content from response.")
            print("Full response:")
            print(content)
            return "Error while parsing JSON content: " + str(e2), content

