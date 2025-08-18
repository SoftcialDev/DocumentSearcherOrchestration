from sentence_transformers import SentenceTransformer
from docx import Document
import fitz
import json
import logging
    
model = SentenceTransformer("all-mpnet-base-v2")

def get_preset(table: str):
    """
    Given a table name, returns the text preset for human readability.

    Args:
        table (str): The name of the database table.

    Returns:
        str: The human-readable preset text corresponding to the table name.
            If no preset is found, it raises an error.
    """
    with open("presets.json", "r", encoding="utf-8") as file:
        values = json.load(file)
        preset = values.get(table, None)
        if preset is None:
            raise ValueError(f"No preset found for table '{table}'")
        return preset
    
def data_to_human(table: str, values: dict):
    """
    Given a table name and a dictionary of values, inject the values into a ready to use preset
    for each table stored in the system.

    Args:
        table (str): The name of the database table.
        values (dict): A one level dictionary that matches keys with the values stored in the system

    Returns:
        str: The human-readable adjusted text corresponding to the table name.
            If no preset is found, it returns None
    """
    preset = get_preset(table)
    if preset:
        human_text = preset.format(**values)
        return human_text
    else:
        return None
    
def string_to_chunks(text: str, max_words=200, overlap=0.2) -> list:
    """
	Reads and splits a string into chunks of delimited sizes.
    
    Args:
		text (str): The text to convert.
        max_words (int): Maximum amount of words per chunck.
        overlap (float): Percentage of words to share with an adjacent chunks to maintain context.
        
    Returns:
		list: A list of str, each str represent a portion of the original text.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = []
    word_count = 0
    max_total = max_words
    step_words = int(max_words * (1 - overlap))

    for paragraph in paragraphs:
        words = paragraph.split()
        if word_count + len(words) > max_total:
            chunks.append(" ".join(current_chunk))
            current_chunk = words[-step_words:]
            word_count = len(current_chunk)
        else:
            current_chunk.extend(words)
            word_count += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def pdf_to_chunks(filepath: str, max_words=200, overlap=0.2) -> list:
    """
	Reads and splits the content of a PDF file into chunks of delimited sizes.
    
    Args:
		filepath (str): The path of the PDF file.
        max_words (int): Maximum amount of words per chunck.
        overlap (float): Percentage of words to share with an adjacent chunks to maintain context.
    Returns:
		list: A list of str, each str represent a portion of the original text.
    """
    logging.info(f"Parsing PDF: {filepath}")
    doc = fitz.open(filepath)
    text = ""

    for page in doc:
        text += page.get_text()

    logging.info(f"Extracted {len(text)} characters from PDF.")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = []
    word_count = 0
    max_total = max_words
    step_words = int(max_words * (1 - overlap))

    for paragraph in paragraphs:
        words = paragraph.split()
        if word_count + len(words) > max_total:
            chunks.append(" ".join(current_chunk))
            current_chunk = words[-step_words:]  # overlap
            word_count = len(current_chunk)
        else:
            current_chunk.extend(words)
            word_count += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logging.info(f"Split into {len(chunks)} chunks.")
    return chunks


def docx_to_chunks(filepath: str, max_words=200, overlap=0.2) -> list:
    """
    Reads and splits the content of a DOCX file into chunks of delimited sizes.
    
    Args:
        filepath (str): The path of the PDF file.
        max_words (int): Maximum amount of words per chunck.
        overlap (float): Percentage of words to share with an adjacent chunks to maintain context.
    Returns:
		list: A list of str, each str represent a portion of the original text.
    """
    
    logging.info(f"Parsing DOCX: {filepath}")
    doc = Document(filepath)
    text = "\n".join([p.text for p in doc.paragraphs])
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    logging.info(f"Extracted {len(text)} characters from DOCX.")
    
    chunks = []
    current_chunk = []
    word_count = 0
    max_total = max_words
    step_words = int(max_words * (1 - overlap))

    logging.info(f"Parsing DOCX: {filepath}")
    for paragraph in paragraphs:
        words = paragraph.split()
        if word_count + len(words) > max_total:
            chunks.append(" ".join(current_chunk))
            current_chunk = words[-step_words:]  # overlap with last part
            word_count = len(current_chunk)
        else:
            current_chunk.extend(words)
            word_count += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logging.info(f"Split into {len(chunks)} chunks.")
    return chunks

def chunks_to_embeddings(chunks: list) -> list:
    """
    Transform a list of chunks into a list of embeddings of 768 dimesions
    
    Args:
        chunks (list): A list containing the chunks to be transformed
    Returns:
		list: A list of tuples where each tuple contains the originsl chunk with their resulted embedding
    """
    embeddings = model.encode(chunks, normalize_embeddings=True)
    return list(zip(chunks, embeddings))