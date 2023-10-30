import streamlit as st

st.set_option(
    "deprecation.showPyplotGlobalUse", False
)  # To suppress MatplotlibDeprecationWarning to display SHAP plot
import pandas as pd
import plotly.express as px
import numpy as np
import yaml
import pickle

# import matplotlib.pyplot as plt
import shap
from tensorflow import keras


# Config the whole app
st.set_page_config(
    page_title="DITTO4NF",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


# Function to open and load config file for filtering columns and rows
@st.cache_data
def get_col_configs(config_f):
    with open(config_f) as fh:
        config_dict = yaml.safe_load(fh)

    # print(config_dict)
    return config_dict


# Class to define colors for Clinvar classification
class ClinSigColors:
    default_colors = {
        "not seen in clinvar": "#969696",
        "other": "#969696",
        "not provided": "#969696",
        "Conflicting interpretations of pathogenicity": "#d8b365",
        "Benign": "#3182bd",
        "Likely benign": "#2166ac",
        "Benign/Likely benign": "#2166ac",
        "Uncertain significance": "#5ab4ac",
        "Uncertain significance, other": "#5ab4ac",
        "Pathogenic/Likely pathogenic": "#b2182b",
        "Likely pathogenic": "#d73027",
        "Pathogenic": "#b2182b",
    }


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


@st.cache_resource
def load_model():
    # Load background data to generate SHAP explainer object
    pkl_file = open(
        "./results/background.pkl",
        "rb",
    )
    background = pickle.load(pkl_file)
    pkl_file.close()

    # Load model and weights
    clf = keras.models.load_model("./results/Neural_network")
    clf.load_weights("./results/weights.h5")

    # Generate SHAP explainer object
    explainer = shap.KernelExplainer(clf.predict, background)
    del clf
    return explainer


@st.cache_data
def load_lovd(config_dict):
    lovd = pd.read_csv(
        "results/lovd_filtered.csv.gz",
        low_memory=False,
    )

    # Extract ID columns along with DITTO score for the plot
    ditto = lovd[config_dict["id_cols"]]

    # Add variant info to a single column
    ditto["var_details"] = (
        ditto["chrom"]
        + ":"
        + ditto["pos"].astype(str)
        + ":"
        + ditto["ref_base"]
        + ">"
        + ditto["alt_base"]
    )

    # Extract feature names for SHAP plot
    feature_names = lovd.drop(config_dict["id_cols"], axis=1).columns

    return lovd, ditto, feature_names


def plot_data(st, data, class_color):
    st.subheader("**Interactive scatter plot with DITTO predictions**")
    st.markdown(
        "- Each dot in the below interactive scatter plot is a"
        " variant-transcript pair i.e. variant positioned on one of the"
        " Ensemble transcripts. Color of each dot represents the"
        " [Clinvar](https://www.ncbi.nlm.nih.gov/clinvar/) classification"
        " denoted by the same color in figure legends."
    )
    st.markdown(
        f"- The red dashed line represents the cutoff of DITTO score to be"
        f" classified as highly deleterious to the protein."
    )
    st.markdown(
        "- Scatterplot is made with [Python Plotly](https://plotly.com/python/)"
        " and is interactive; can be viewed in full screen."
    )
    st.write(f"Total variants = {len(data)}")

    data["clinvar.sig"] = data["clinvar.sig"].replace(np.nan, "not seen in clinvar")
    data = data.replace(np.nan, "N/A")

    # Sort the data by clinvar classification by categorizing them using the class_color dictionary. This is to make
    # sure only the clinvar class in the data are shown in the plot.
    class_list = [
        tuple for x in class_color.keys() for tuple in data["clinvar.sig"].unique() if tuple == x
    ]

    data["clinvar.sig"] = data["clinvar.sig"].astype("category")
    data["clinvar.sig"] = data["clinvar.sig"].cat.set_categories(class_list)
    data = data.sort_values(["clinvar.sig"])

    # Calculate cutoff
    cutoff = data[data["clinvar.sig"].dropna(how="all").isin(["Likely pathogenic"])]["DITTO"].mean()
    cutoff = round(cutoff, 2)

    st.write(f"Deleterious cutoff value = {cutoff}")

    # Scatter plot with DITTO score
    data1 = px.scatter(
        data,
        x="pos",
        y="DITTO",
        color="clinvar.sig",
        # opacity=0.3,
        hover_data=[
            "consequence",
            "var_details",
            "transcript",
            "clinvar.sig",
            "clingen.classification",
            "clinvar.sig_conf",
            "clinvar.rev_stat",
        ],
        hover_name="protein_hgvs",
        labels={
            "pos": "Position",
            "DITTO": "DITTO Deleterious Score",
            "clinvar.sig": "Clinvar Classification",
            "clinvar.sig_conf": "Clinvar Confidence",
            "clinvar.rev_stat": "Clinvar review status",
        },
        color_discrete_map=class_color,
    )
    data1.update_layout(xaxis_tickformat="f")

    # Add cutoff line
    data1.add_hline(y=cutoff, line_width=2, line_dash="dash", line_color="red")
    data1.update_layout(legend_traceorder="reversed")

    st.plotly_chart(data1, use_container_width=True)
    return None


def main():
    st.header(f"DITTO deleterious prediction with explanations for LOVD NF1 variants")

    # Load the config file as dictionary
    config_f = "./configs/app_cols.yaml"
    config_dict = get_col_configs(config_f)

    # Load the model and data
    df2, var, feature_names = load_lovd(config_dict)
    explainer = load_model()

    # Filter data depending on transcript selected
    transcript = st.sidebar.selectbox("Choose transcript:", options=df2["transcript"].unique())
    lovd = df2[df2["transcript"] == transcript].reset_index(drop=True)
    overall = var[var["transcript"] == transcript].reset_index(drop=True)

    # Choose prediction display option
    display_data = st.sidebar.selectbox(
        "Choose prediction display option:", options=["Plot", "Table"]
    )
    if display_data == "Table":
        st.dataframe(overall)
    else:
        plot_data(st, overall, ClinSigColors.default_colors)

    # Download DITTO predictions
    st.sidebar.download_button(
        label=f"Download DITTO predictions",
        data=convert_df(overall),
        file_name=f"DITTO_LOVD_predictions.csv",
        mime="text/csv",
    )

    # Filter variant from data and display variant information for SHAP plot
    st.subheader("**DITTO Explanations using SHAP**")
    st.markdown(
        "Please choose table view option in sidebar to display necessary"
        " variant information that can be used to generate SHAP plot."
    )
    col1, col2 = st.columns([1, 2])
    chrom = col1.selectbox("Chromosome:", options=overall["chrom"].unique())
    pos = col1.selectbox(
        "Position:",
        options=overall[(overall.chrom == chrom)]["pos"].unique(),
    )
    ref = col1.selectbox(
        "Reference Nucleotide:",
        options=overall[(overall.chrom == chrom) & (overall.pos == pos)]["ref_base"].unique(),
    )
    alt = col1.selectbox(
        "Alternate Nucleotide:",
        options=overall[
            (overall.chrom == chrom) & (overall.pos == pos) & (overall.ref_base == ref)
        ]["alt_base"].unique(),
    )
    ditto = overall[
        (overall.chrom == chrom)
        & (overall.pos == pos)
        & (overall.ref_base == ref)
        & (overall.alt_base == alt)
    ]

    annots = (
        lovd[
            (lovd.chrom == chrom)
            & (lovd.pos == pos)
            & (lovd.ref_base == ref)
            & (lovd.alt_base == alt)
        ]
        .drop(config_dict["id_cols"], axis=1)
        .reset_index(drop=True)
    )

    # initialise data of lists to print on the webpage.
    var_scores = {
        "Source": [
            "DITTO score",
            "Clinvar Classification",
            "Clingen Classification",
            "gnomAD AF",
        ],
        "Values": [
            # str(round(1 - (ditto["DITTO"].values[0]), 2)),
            str(ditto["DITTO"].values[0]),
            ditto["clinvar.sig"].values[0],
            ditto["clingen.classification"].values[0],
            annots["gnomad3.af"].values[0],
        ],
    }
    # Create DataFrame
    col1.dataframe(pd.DataFrame(var_scores))

    # SHAP explanation
    shap_value = explainer.shap_values(annots.values)[0]

    # SHAP explanation plot for a variant
    col2.pyplot(
        shap.plots._waterfall.waterfall_legacy(
            1 - explainer.expected_value[0],  # DITTO prediction for deleterious is (1 - y_pred)
            np.negative(shap_value[0]),  # SHAP value for deleterious is negative
            annots.values[0],
            feature_names,
            max_display=20,
        )
    )


if __name__ == "__main__":
    main()
