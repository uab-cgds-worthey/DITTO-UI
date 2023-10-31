from pathlib import Path
import argparse
import os
import json
import yaml
import pandas as pd


class OCApiParser:
    def __init__(self, parsing_config, column_config) -> None:
        self.parsing_config = parsing_config
        self.column_config = column_config

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
                dict_of_dicts[trx_index_keys[index]][data_field_name] = data_value

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

            ret_list.append(var_trx)

        return ret_list

    def query_variant(self, chrom: str, pos: int, ref: str, alt: str) -> pd.DataFrame:
        pass


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
        description="Simple parser for creating data model, data parsing config, and data parsing of annotations from OpenCravat",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    PARSER.add_argument(
        "-i",
        "--input_csv",
        help="File path to the CSV file of annotated variants from OpenCravat",
        required=True,
        type=lambda x: is_valid_file(PARSER, x),
        metavar="\b",
    )

    PARSER.add_argument(
        "-e",
        "--exec",
        help="Determine what should be done: create a new data config file or parse the annotations from the OpenCravat CSV file",
        required=True,
        choices=EXECUTIONS,
        metavar="\b",
    )

    OPTIONAL_ARGS = PARSER.add_argument_group("Override Args")
    PARSER.add_argument(
        "-o",
        "--output",
        help="Output directory for parsing",
        type=lambda x: is_valid_output_dir(PARSER, x),
        metavar="\b",
    )

    PARSER.add_argument(
        "-v",
        "--version",
        help="Verison of OpenCravat used to generate the config file (only required during config parsing)",
        type=str,
        metavar="\b",
    )

    PARSER.add_argument(
        "-c",
        "--config",
        help="File path to the data config JSON file that determines how to parse annotated variants from OpenCravat",
        type=lambda x: is_valid_file(PARSER, x),
        metavar="\b",
    )

    ARGS = PARSER.parse_args()

    if ARGS.exec == "config" and not ARGS.version:
        print(
            "Version of OpenCravat must be specified when creating a config from their data for tracking purposes"
        )
        raise SystemExit(1)

    if ARGS.exec == "config":
        create_data_config(ARGS.input_csv, f"opencravat_{ARGS.version}_config.json")
    else:
        outdir = Path(ARGS.output) if ARGS.output else Path(ARGS.input_csv).parent
        parse_annotations(ARGS.input_csv, ARGS.config, outdir)
