import xml.etree.ElementTree as ET
from lxml.etree import XMLParser
from typing import List, Dict

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
