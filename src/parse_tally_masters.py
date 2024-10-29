import xml.etree.ElementTree as ET
from lxml.etree import XMLParser
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import torch
import pandas as pd

type MasterData = Dict[str, List[str]]


def parse_tally_masters(xml_file: str):
    """
    Master data that can be extracted from Tally XML:
    COMPANY, COSTCATEGORY, CURRENCY, GODOWN, GROUP, INCOMETAXCLASSIFICATION
    INCOMETAXSLAB, LEDGER, STOCKGROUP, STOCKITEM, TAXUNIT, UNIT, VOUCHERTYPE
    """

    parser = XMLParser(recover=True)
    tree = ET.parse(xml_file, parser=parser)
    masters = tree.findall(".//TALLYMESSAGE")
    master_data: MasterData = {}

    for master in masters:
        for child in master:
            if master_data.get(child.tag) is None:
                master_data[child.tag] = []

            name = child.attrib.get("NAME")
            if name is not None:
                master_data[child.tag].append(name)

    return master_data


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


# TODO: Match units and other fields
def match_masters(
    masters_data: MasterData, common_df: pd.DataFrame, item_df: pd.DataFrame
):
    supplier_name = common_df["Supplier Name"].iloc[0]
    supplier_ledger_name = find_closest_match(supplier_name, masters_data["LEDGER"])
    common_df["Supplier Ledger Name"] = supplier_ledger_name

    item_df["Stock Item"] = item_df["Product Name"].apply(
        lambda x: find_closest_match(x, masters_data["STOCKITEM"])
    )

    return common_df, item_df
