import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF


def content_crawler(url, file_format='txt', output_file='privacy_policy'):
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.find_all(['h2', 'p', 'i', 'ul'])

        # Create output folder if it doesn't exist
        if not os.path.exists('../learning_documents'):
            os.makedirs('../learning_documents')

        # Save content based on the specified file format
        output_path = os.path.join('../learning_documents', output_file)

        if file_format == 'txt':
            with open(f"{output_path}.txt", "w", encoding="utf-8") as file:
                for t in text:
                    file.write(f'{t.text}\n')
            print(f"Content saved to {output_path}.txt")
        elif file_format == 'pdf':
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", "B", 8)
            for t in text:
                pdf.cell(0, 10, t.text, ln=True)
            pdf.output(f"{output_path}.pdf")
            print(f"Content saved to {output_path}.pdf")
        elif file_format == 'csv':
            df = pd.DataFrame({'Content': [t.text for t in text]})
            df.to_csv(f"{output_path}.csv", index=False)
            print(f"Content saved to {output_path}.csv")
        elif file_format == 'xml':
            xml_content = ''.join([f'<item>{t.text}</item>' for t in text])
            with open(f"{output_path}.xml", "w", encoding="utf-8") as file:
                file.write(f'<root>{xml_content}</root>')
            print(f"Content saved to {output_path}.xml")
        else:
            print("Invalid file format. Supported formats: txt, pdf, csv, xml")
    else:
        print("Failed to retrieve content from the URL.")


if __name__ == '__main__':
    pass
    # Example usage:
    # content_crawler("https://www.presight.io/privacy-policy.html", file_format='pdf', output_file='privacy_policy')
