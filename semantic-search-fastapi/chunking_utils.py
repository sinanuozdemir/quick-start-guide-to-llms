# Importing the tiktoken library
import re

import PyPDF2
import tiktoken
from tqdm import tqdm

# Initializing a tokenizer for the 'cl100k_base' model
# This tokenizer is designed to work with the 'ada-002' embedding model
tokenizer = tiktoken.get_encoding("cl100k_base")


# Function to split the text into chunks of a maximum number of tokens. Inspired by OpenAI
def overlapping_chunks(text, max_tokens=500, overlapping_factor=5):
    '''
    max_tokens: tokens we want per chunk
    overlapping_factor: number of sentences to start each chunk with that overlaps with the previous chunk
    '''

    # Split the text using punctuation
    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)

    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]

    chunks, tokens_so_far, chunk = [], 0, []

    # Loop through the sentences and tokens joined together in a tuple
    for sentence, token in zip(sentences, n_tokens):
        print(sentence, token)

        # If the number of tokens so far plus the number of tokens in the current sentence is greater
        # than the max number of tokens, then add the chunk to the list of chunks and reset
        # the chunk and tokens so far
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            if overlapping_factor > 0:
                chunk = chunk[-overlapping_factor:]
                tokens_so_far = sum([len(tokenizer.encode(c)) for c in chunk])
            else:
                chunk = []
                tokens_so_far = 0

        # If the number of tokens in the current sentence is greater than the max number of
        # tokens, go to the next sentence
        if token > max_tokens:
            continue

        # Otherwise, add the sentence to the chunk and add the number of tokens to the total
        chunk.append(sentence)
        tokens_so_far += token + 1
    if chunk:
        chunks.append(". ".join(chunk) + ".")

    return chunks
