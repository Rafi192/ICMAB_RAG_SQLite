from bs4 import BeautifulSoup
import re


def strip_html(text:str) -> str:
    #removing HTML tags, decoding entities, normalize whitespace
    if not text:
        return ""
    
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get(separator=" ")
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def normalize(text:str)-> str:

    #lowercase , remove special chars except punctuation

    text = strip_html(text)
    text = re.sub(r'[^\w\s\.\,\?\!\-\(\)]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()