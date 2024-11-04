from typing import List
from sentence_transformers import SentenceTransformer
import torch
import pandas as pd


def find_closest_matches(sentences: List[str], choices: List[str]) -> List[str]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer("all-mpnet-base-v2").to(device)

    sentences_embeddings = model.encode(sentences, convert_to_tensor=True)
    choices_embeddings = model.encode(choices, convert_to_tensor=True)

    # ? Calculate similarities between all sentences and choices
    similarities = torch.cosine_similarity(
        sentences_embeddings.unsqueeze(1),  # Shape: (num_sentences, 1, embedding_dim)
        choices_embeddings.unsqueeze(0),  # Shape: (1, num_choices, embedding_dim)
        dim=2,
    )  # Shape: (num_sentences, num_choices)
    similarities = similarities.cpu().detach().numpy()

    # ? Find best matches with probability threshold
    min_similarity = 0.9
    matches = []

    for similarity in similarities:
        max_similarity_idx = similarity.argmax()
        top_choice = choices[max_similarity_idx]
        top_choice_prob = similarity[max_similarity_idx]
        match = top_choice if top_choice_prob >= min_similarity else None
        matches.append(match)

    return matches


def batch_match_column(df_col: pd.Series, choices: List[str]):
    # Convert Series to list for batch processing
    unique_units = df_col.unique().tolist()

    # Get matches for unique values
    unique_matches = find_closest_matches(unique_units, choices)
    unit_mapping = dict(zip(unique_units, unique_matches))

    matched_units = df_col.map(unit_mapping)

    return matched_units
