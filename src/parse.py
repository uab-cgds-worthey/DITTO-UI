from pathlib import Path
import argparse
import os
import json


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
                        "gene": gene,
                        "transcript": var_trx[3],
                        "consequence": var_trx[2],
                        "protein_hgvs": var_trx[1],
                        "cdna_hgvs": var_trx[4],
                    }
                )

        return mappings

    def _parse_list_of_dicts(self, oc_response_dict, column_config):
        col_keys = column_config["col_id"].split(".")
        dict_of_dicts = dict()
        if not oc_response_dict[col_keys[0]]:
            return dict_of_dicts

        for sublist in oc_response_dict[col_keys[0]][col_keys[1]]:
            sublist_dict = dict()
            trx_id = sublist[column_config["trx_mapping_col_index"]].split(".")[0]
            dict_of_dicts[trx_id] = sublist_dict
            for index, value in enumerate(sublist):
                # look up column name by index value, assign column name as key in return dict
                if str(index) not in column_config["dict_index"]:
                    continue

                sublist_dict[column_config["dict_index"][str(index)]] = value

        return dict_of_dicts

    def _parse_multicolumn_list_of_dicts(
        self, index_column, multi_column_config, data_cols_dict
    ):
        # data_cols_n_configs => list of tuples where tuple[0] is column value, tuple[1] is column config
        index_mapping = dict()
        dict_of_dicts = dict()

        if index_column == "":
            return dict_of_dicts

        for index, index_value in enumerate(
            index_column.split(multi_column_config["separator"])
        ):
            index_mapping[index] = index_value.split(".")[0]
            dict_of_dicts[index_mapping[index]] = dict()

        for column, value in data_cols_dict.items():
            sublist = value.split(multi_column_config["separator"])
            for index, data_value in enumerate(sublist):
                dict_of_dicts[index_mapping[index]][column] = data_value

        return dict_of_dicts

    def parse_oc_api_json(self, annot_json_string: str) -> list:
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
