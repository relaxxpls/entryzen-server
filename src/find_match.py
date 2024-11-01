from typing import List
from sentence_transformers import SentenceTransformer
import torch


def find_closest_match(sentence: str, choices: List[str]):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer("all-mpnet-base-v2").to(device)

    sentence_embedding = model.encode([sentence], convert_to_tensor=True)
    choices_embeddings = model.encode(choices, convert_to_tensor=True)

    text_similarities = torch.cosine_similarity(sentence_embedding, choices_embeddings)
    text_similarities = text_similarities.cpu().detach().numpy()

    min_similarity = 0.8
    top_choice = choices[text_similarities.argmax()]
    top_choice_prob = text_similarities.max()

    return top_choice if top_choice_prob >= min_similarity else None
