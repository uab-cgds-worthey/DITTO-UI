from pathlib import Path
import argparse
import os
import json
import yaml
import pandas as pd
import requests


class OCApiParser:
    def __init__(self, parsing_config) -> None:
        self.parsing_config = parsing_config

    def _parse_all_mappings(self, oc_response_dict):
        if (not oc_response_dict["crx"]["all_mappings"]) or oc_response_dict["crx"][
            "all_mappings"
        ] == "":
            return []

        mappings = []
        parsed_all_mappings = json.loads(oc_response_dict["crx"]["all_mappings"])
        for gene, var_trxs in parsed_all_mappings.items():
            for var_trx in var_trxs:
                mappings.append(
                    {
                        "chrom": oc_response_dict["crx"]["chrom"],
                        "pos": oc_response_dict["crx"]["pos"],
                        "ref_base": oc_response_dict["crx"]["ref_base"],
                        "alt_base": oc_response_dict["crx"]["alt_base"],
                        "coding": oc_response_dict["crx"]["coding"],
                        "gene": gene,
                        "transcript": var_trx[3],
                        "consequence": var_trx[2],
                        "protein_hgvs": var_trx[1],
                        "cdna_hgvs": var_trx[4],
                    }
                )

        return mappings

    def _parse_list_of_dicts(
        self,
        data_src,
        data_list_field_name,
        trx_mapping_col_index,
        field_indexs,
        oc_response_dict,
    ):
        dict_of_dicts = dict()
        if not oc_response_dict[data_src]:
            return dict_of_dicts

        for sublist in oc_response_dict[data_src][data_list_field_name]:
            trx_id = sublist[trx_mapping_col_index].split(".")[0]
            dict_of_dicts[trx_id] = {
                data_field_name: sublist[int(index)]
                for index, data_field_name in field_indexs.items()
            }

        return dict_of_dicts

    def _parse_indexed_list(
        self, data_src, index_field_name, data_fields, value_sep, oc_response_dict
    ):
        if not oc_response_dict[data_src]:
            return dict()

        trx_index_keys = [
            key.split(".")[0]
            for key in oc_response_dict[data_src][index_field_name].split(value_sep)
        ]
        dict_of_dicts = {trx: dict() for trx in trx_index_keys}

        for data_field in data_fields:
            data_field_name = data_field.split(".")[1]
            for index, data_value in enumerate(
                oc_response_dict[data_src][data_field_name].split(value_sep)
            ):
                dict_of_dicts[trx_index_keys[index]][data_field] = data_value

        return dict_of_dicts

    def _parse_normal_field(self, data_src, data_field_name, oc_response_dict):
        if not oc_response_dict[data_src]:
            return None

        return oc_response_dict[data_src][data_field_name]

    def parse_oc_api_json(self, annotations_dict: str) -> list:
        listy_fields_mapping = []

        # parse out list type fields
        for list_field_config in filter(
            lambda feild_config: "list" in feild_config["parse_type"],
            self.parsing_config,
        ):
            data_source = list_field_config["col_id"].split(".")[0]
            trx_index_field = list_field_config["parse_type"]["list"][
                "trx_index_col"
            ].split(".")[1]
            field_separator = list_field_config["parse_type"]["list"]["separator"]
            data_fields = list_field_config["parse_type"]["list"]["column_list"]
            listy_fields_mapping.append(
                self._parse_indexed_list(
                    data_src=data_source,
                    index_field_name=trx_index_field,
                    data_fields=data_fields,
                    value_sep=field_separator,
                    oc_response_dict=annotations_dict,
                )
            )

        # parse out list of dicts fields
        for list_field_config in filter(
            lambda feild_config: "list-o-dicts" in feild_config["parse_type"],
            self.parsing_config,
        ):
            data_source_cols = list_field_config["col_id"].split(".")
            trx_col_index = list_field_config["parse_type"]["list-o-dicts"][
                "trx_mapping_col_index"
            ]
            data_fields = list_field_config["parse_type"]["list-o-dicts"]["dict_index"]
            listy_fields_mapping.append(
                self._parse_list_of_dicts(
                    data_src=data_source_cols[0],
                    data_list_field_name=data_source_cols[1],
                    trx_mapping_col_index=trx_col_index,
                    field_indexs=data_fields,
                    oc_response_dict=annotations_dict,
                )
            )

        # parse regular fields
        reg_fields = dict()
        for reg_field in filter(
            lambda feild_config: "none" in feild_config["parse_type"],
            self.parsing_config,
        ):
            cols = reg_field["col_id"].split(".")
            reg_fields[reg_field["col_id"]] = self._parse_normal_field(
                data_src=cols[0],
                data_field_name=cols[1],
                oc_response_dict=annotations_dict,
            )

        # iterate all mappings listing which provides all variant + transcript combo info to build return list
        ret_list = []
        for var_trx in self._parse_all_mappings(annotations_dict):
            var_trx.update(reg_fields)
            trx_key = var_trx["transcript"].split(".")[0]
            for listy_dict in listy_fields_mapping:
                if trx_key in listy_dict:
                    var_trx.update(listy_dict[trx_key])

            # add None values for any fields not annotated
            for list_field_config in filter(
                lambda feild_config: "list-o-dicts" in feild_config["parse_type"],
                self.parsing_config,
            ):
                for data_field in list_field_config["parse_type"]["list-o-dicts"][
                    "dict_index"
                ].values():
                    if data_field not in var_trx:
                        var_trx[data_field] = None

            for list_field_config in filter(
                lambda feild_config: "list" in feild_config["parse_type"],
                self.parsing_config,
            ):
                for data_field in list_field_config["parse_type"]["list"][
                    "column_list"
                ]:
                    if data_field not in var_trx:
                        var_trx[data_field] = None

            ret_list.append(var_trx)

        return ret_list

    def query_variant(self, chrom: str, pos: int, ref: str, alt: str) -> pd.DataFrame:
        if not chrom.startswith("chr"):
            chrom = "chr" + chrom
        url = (
            f"https://run.opencravat.org/submit/annotate?chrom={chrom}&pos={str(pos)}&ref_base={ref}&alt_base={alt}"
            "&annotators=aloft,alt_base,cadd,cancer_genome_interpreter,ccre_screen,cgc,cgd,chasmplus,chrom,civic,"
            "clingen,clinpred,clinvar,coding,cosmic,cosmic_gene,cscape,dann,dann_coding,dbscsnv,dbsnp,dgi,"
            "ensembl_regulatory_build,ess_gene,exac_gene,fathmm,fathmm_xf_coding,funseq2,genehancer,gerp,ghis,"
            "gnomad,gnomad3,gnomad_gene,gtex,gwas_catalog,linsight,loftool,lrt,mavedb,metalr,metasvm,"
            "mutation_assessor,mutationtaster,mutpred1,mutpred_indel,ncbigene,ndex,ndex_chd,ndex_signor,"
            "omim,pangalodb,phastcons,phdsnpg,phi,phylop,polyphen2,pos,prec,provean,ref_base,repeat,revel,"
            "rvis,segway,sift,siphy,spliceai,uniprot,varity_r,vest,transcript,gene,consequence,protein_hgvs,"
            "cdna_hgvs"
        )

        get_fields = requests.get(url, timeout=20)
        try:
            get_fields.raise_for_status()
        except requests.exceptions.RequestException as expt:
            print(
                f"Could not get OpenCravat Annotations for chrom={chrom} pos={str(pos)} ref_base={ref} alt_base={alt}"
            )
            raise expt

        return pd.DataFrame(self.parse_oc_api_json(get_fields.json()))


def is_valid_output_dir(p, arg):
    if os.access(Path(os.path.expandvars(arg)), os.W_OK):
        return os.path.expandvars(arg)
    else:
        p.error(f"Output directory {arg} can't be accessed or is invalid!")


def is_valid_file(p, arg):
    if not Path(os.path.expandvars(arg)).is_file():
        p.error(f"The file {arg} does not exist!")
    else:
        return os.path.expandvars(arg)


if __name__ == "__main__":
    EXECUTIONS = [
        "config",
        "parse",
    ]

    PARSER = argparse.ArgumentParser(
        description="Easy testing of data parsing of annotations from OpenCravat API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    PARSER.add_argument(
        "-i",
        "--input",
        help="File path to the JSON file of annotated variant from OpenCravat API",
        required=False,
        type=lambda x: is_valid_file(PARSER, x),
        metavar="\b",
    )

    PARSER.add_argument(
        "-v",
        "--variant",
        help="Variant in 'chr_pos_ref_alt' format to be annotated from OpenCravat API",
        required=False,
        type=str,
        metavar="\b",
    )

    ARGS = PARSER.parse_args()

    repo_root = Path(__file__).parent.parent

    data_config = repo_root / "configs" / "opencravat_test_config.json"
    data_config_dict = None
    with data_config.open("rt") as dc_fp:
        data_config_dict = json.load(dc_fp)

    parser = OCApiParser(data_config_dict)

    if ARGS.input:
        test_file = Path(ARGS.input)
        annotation_data = None
        with test_file.open("rt") as ex_fp:
            annotation_data = json.load(ex_fp)

        print(parser.parse_oc_api_json(annotation_data))
    else:
        varinfo = ARGS.variant.split("_")
        dataframe = parser.query_variant(
            chrom=varinfo[0], pos=int(varinfo[1]), ref=varinfo[2], alt=varinfo[3]
        )
        print(dataframe)
