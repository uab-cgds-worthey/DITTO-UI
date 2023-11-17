import pandas as pd
import numpy as np

def parse_and_predict(dataframe, config_dict, clf):
    # Drop variant info columns so we can perform one-hot encoding
    dataframe["so"] = dataframe["consequence"]
    var = dataframe[config_dict["id_cols"]]
    var["gnomad3.af"] = dataframe["gnomad3.af"].copy()
    dataframe = dataframe.drop(config_dict["id_cols"], axis=1)
    dataframe = dataframe.replace(['.','-',''], np.nan)
    for key in dataframe.columns:
        try:
            dataframe[key] = dataframe[key].astype("float64")
        except:
            pass
    temp_df = dataframe.copy()
    # Perform one-hot encoding
    for key in config_dict["dummies_sep"]:
        if not dataframe[key].isnull().all():
            dataframe = pd.concat(
            (dataframe, dataframe[key].str.get_dummies(sep=config_dict["dummies_sep"][key])), axis=1
        )

    dataframe = dataframe.drop(list(config_dict["dummies_sep"].keys()), axis=1)
    dataframe = pd.get_dummies(dataframe, prefix_sep="_")

    dataframe = dataframe*1
    df2 = pd.DataFrame(columns=config_dict["filtered_cols"])
    for key in config_dict["filtered_cols"]:
        if key in dataframe.columns:
            df2[key] = dataframe[key]
        else:
            df2[key] = 0
    del dataframe

    df2 = df2.drop(config_dict["train_cols"], axis=1)
    for key in list(config_dict["median_scores"].keys()):
        if key in df2.columns:
            df2[key] = df2[key].fillna(config_dict["median_scores"][key]).astype("float64")

    y_score = 1 - clf.predict(df2, verbose=0)
    #y_score = pd.DataFrame(y_score, columns=["DITTO"])

    #var = pd.concat([var.reset_index(drop=True), y_score.reset_index(drop=True)], axis=1)
    #dataframe = pd.concat([var.reset_index(drop=True), temp_df.reset_index(drop=True)], axis=1)
    del temp_df, var
    return df2, y_score
