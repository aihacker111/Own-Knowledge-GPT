from bs4 import BeautifulSoup
from urllib import request
from bot.web_scrapping.searchable_index import SearchableIndex
from bot.utils.show_log import logger
import requests
import os


def save_content_to_file(url=None, text=None, output_folder=None, file_format=None):
    file_path = os.path.join(output_folder, f"combined_content.{file_format}")

    write_functions = {
        'txt': lambda: write_text(file_path, text),
        'pdf': lambda: write_pdf(url, file_path)
    }

    write_function = write_functions.get(file_format)
    if write_function:
        write_function()
        logger.info(f"Content appended to {file_path}")
    else:
        logger.warning("Invalid file format. Supported formats: txt, pdf, csv, xml")

    return file_path


def write_text(file_path, text):
    with open(file_path, "a", encoding="utf-8") as file:
        for t in text:
            file.write(f'{t.text}\n')


def write_pdf(url, file_path):
    request.urlretrieve(url, file_path)


def content_crawler_and_index(url, llm, prompt, file_format='txt', output_folder='learning_documents'):
    if url == 'NO_URL':
        file_path = output_folder
    else:
        responses = requests.get(url)
        if responses.status_code != 200:
            logger.warning("Failed to retrieve content from the URL.")
            return None
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        soup = BeautifulSoup(responses.text, "html.parser")
        text = soup.find_all(['h2', 'p', 'i', 'ul'])
        file_path = save_content_to_file(text=text, url=url, output_folder=output_folder, file_format=file_format)

    index = SearchableIndex.embed_index(url=url, path=file_path, llm=llm, prompt=prompt)
    if url != 'NO_URL' and os.path.isfile(file_path):
        os.remove(file_path)

    return index


if __name__ == '__main__':
    pass
