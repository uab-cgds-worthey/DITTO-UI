from parse import OCApiParser
import json
from pathlib import Path

repo_root = Path(__file__).parent.parent

data_config = repo_root / "configs" / "opencravat_test_config.json"
data_config_dict = None
with data_config.open("rt") as dc_fp:
    data_config_dict = json.load(dc_fp)
parser = OCApiParser(data_config_dict)
variant = '6_26090951_C_G'
varinfo = variant.split("_")
dataframe = parser.query_variant(
            chrom=varinfo[0], pos=int(varinfo[1]), ref=varinfo[2], alt=varinfo[3]
        )
print(dataframe)
