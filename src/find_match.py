from typing import List, Optional
from sentence_transformers import SentenceTransformer
import torch
import pandas as pd


def find_closest_matches(
    sentences: List[str] | pd.Series, choices: List[str]
) -> List[Optional[str]]:
    if isinstance(sentences, pd.Series):
        sentences = sentences.tolist()
    if len(sentences) == 0:
        return []
    if len(choices) == 0:
        return [None] * len(sentences)

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer("all-mpnet-base-v2").to(device)

        sentences_embeddings = model.encode(sentences, convert_to_tensor=True)
        choices_embeddings = model.encode(choices, convert_to_tensor=True)

        sentences_embeddings = sentences_embeddings.to(device)
        choices_embeddings = choices_embeddings.to(device)

        # Calculate similarities between all sentences and choices
        similarities = torch.cosine_similarity(
            sentences_embeddings.unsqueeze(1),  # (num_sentences, 1, embedding_dim)
            choices_embeddings.unsqueeze(0),  # (1, num_choices, embedding_dim)
            dim=2,
        )  # (num_sentences, num_choices)

        # Move to CPU for numpy operations
        similarities = similarities.cpu().detach().numpy()

        # Find best matches with probability threshold
        min_similarity = 0.9
        matches = []

        for similarity in similarities:
            max_similarity_idx = similarity.argmax()
            top_choice = choices[max_similarity_idx]
            top_choice_prob = similarity[max_similarity_idx]
            match = top_choice if top_choice_prob >= min_similarity else None
            matches.append(match)

        return matches

    except Exception as e:
        print(f"Error in find_closest_matches: {str(e)}")
        return [None] * len(sentences)


def batch_match_column(df_col: pd.Series, choices: List[str]):
    # Convert Series to list for batch processing
    unique_units = df_col.dropna().unique()

    # Get matches for unique values
    unique_matches = find_closest_matches(unique_units, choices)
    unit_mapping = dict(zip(unique_units, unique_matches))

    result = df_col.apply(lambda x: unit_mapping.get(str(x)) if pd.notna(x) else None)

    return result
