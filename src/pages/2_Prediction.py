import streamlit as st

st.set_option(
    "deprecation.showPyplotGlobalUse", False
)  # To suppress MatplotlibDeprecationWarning to display SHAP plot
import pandas as pd
import plotly.express as px
import numpy as np
import yaml
import pickle

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
# @st.cache_data
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
    return explainer, clf


def query_external_api(api_url):
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    response = http.get(api_url, headers=headers)

    # raise exception if 4XX or 5XX status code returned from server after 3 retries
    resp_dict = None
    try:
        response.raise_for_status()
        resp_dict = response.json()
    except requests.exceptions.RequestException as expt:
        print(
            f"Failed to query {api_url}, code: {response.status_code}, reason: {response.reason},"
            f" text: {response.text}, error: {str(expt)}"
        )
    finally:
        http.close()  # this will release resources so that the GC can clean up the request and response objects

    return resp_dict


@st.cache_data(
    ttl=3600
)  # expire cached results of the Uniprot query after 1 hour for the requested gene
def get_domain(gene_name):
    uniprot_url = f"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:{gene_name}+AND+organism_id:9606&format=json&fields=ft_domain,cc_domain,protein_name"
    info_dict = query_external_api(uniprot_url)

    # set defaults for uniprot return information
    fullname = ""
    domain = []

    if len(info_dict["results"]) > 0:
        first_rec = info_dict["results"][0]
        if "recommendedName" in first_rec.get("proteinDescription"):
            fullname = (
                first_rec.get("proteinDescription")
                .get("recommendedName")
                .get("fullName")
                .get("value")
            )
        elif "submissionNames" in first_rec.get("proteinDescription"):
            fullname = (
                first_rec.get("proteinDescription")
                .get("submissionNames")[0]
                .get("fullName")
                .get("value")
            )

        for feature in info_dict["results"][0]["features"]:
            if feature["type"] == "Domain":
                domain.append(
                    {
                        "type": "Domain",
                        "description": feature["description"],
                        "start": int(feature["location"]["start"]["value"]),
                        "end": int(feature["location"]["end"]["value"]),
                    }
                )

    if len(domain) == 0:
        domain.append({"type": "Domain", "description": "", "start": 0, "end": 0})

    del info_dict
    return fullname, pd.DataFrame(domain)


@st.cache_data(
    ttl=3600
)  # expire cached results of the Uniprot query after 1 hour for the requested gene
def oc_api(chrom="1", pos=2406483, ref="C", alt="G"):
    uniprot_url = f"https://run.opencravat.org/submit/annotate?chrom=chr{chrom}&pos={pos}&ref_base={ref}&alt_base={alt}&annotators=aloft,cadd,cadd_exome,cancer_genome_interpreter,ccre_screen,chasmplus,civic,clingen,clinpred,clinvar,cosmic,cosmic_gene,cscape,dann,dann_coding,dbscsnv,dbsnp,dgi,ensembl_regulatory_build,ess_gene,exac_gene,fathmm,fathmm_xf_coding,funseq2,genehancer,gerp,ghis,gnomad,gnomad3,gnomad_gene,gtex,gwas_catalog,linsight,loftool,lrt,mavedb,metalr,metasvm,mutation_assessor,mutationtaster,mutpred1,mutpred_indel,ncbigene,ndex,ndex_chd,ndex_signor,omim,pangalodb,phastcons,phdsnpg,phi,phylop,polyphen2,prec,provean,repeat,revel,rvis,segway,sift,siphy,spliceai,uniprot,vest,cgc,cgd,varity_r"
    info_dict = query_external_api(uniprot_url)
    return info_dict


def get_annots(info_dict, config_dict):
    current_data = {}

    for key in config_dict:
        if key in info_dict:
            current_data[key] = info_dict[key]
        else:
            # Handle the case where the key is not present in the dictionary
            current_data[key] = None
    return current_data


def main():
    st.header(f"DITTO deleterious prediction with explanations")

    # Load the config file as dictionary
    config_f = "./configs/col_config.yaml"
    config_dict = get_col_configs(config_f)

    # Load the model and data
    # df2, var, feature_names = load_lovd(config_dict)
    explainer, clf = load_model()

    # # Filter data depending on transcript selected
    # transcript = st.sidebar.selectbox("Choose transcript:", options=df2["transcript"].unique())
    # lovd = df2[df2["transcript"] == transcript].reset_index(drop=True)
    # overall = var[var["transcript"] == transcript].reset_index(drop=True)

    # # Download DITTO predictions
    # st.sidebar.download_button(
    #     label=f"Download DITTO predictions",
    #     data=convert_df(overall),
    #     file_name=f"DITTO_LOVD_predictions.csv",
    #     mime="text/csv",
    # )

    col1, col2, col3, col4 = st.columns(4)
    chrom = col1.selectbox("Chromosome:", options=list(range(1, 22)) + ["X", "Y", "MT"])
    pos = col2.text_input("Position:", 2406483)
    ref = col3.text_input("Reference Nucleotide:", "C")
    alt = col4.text_input("Alternate Nucleotide:", "G")

    # Filter variant from data and display variant information for SHAP plot
    st.subheader("**DITTO Explanations using SHAP**")
    st.markdown(
        "Please choose table view option in sidebar to display necessary"
        " variant information that can be used to generate SHAP plot."
    )
    # if chrom & pos & ref & alt:
    info_dict = oc_api(chrom, int(pos), ref, alt)
    annot_col1, annot_col2, annot_col3, annot_col4 = st.columns(4)
    annot_col1.subheader("Allele Frequencies")
    AF_data = get_annots(info_dict, config_dict["display_cols"]["AF"])
    annot_col1.write(AF_data)

    annot_col2.subheader("Conservation scores")
    cons_data = get_annots(info_dict, config_dict["display_cols"]["cons"])
    annot_col2.write(cons_data)

    annot_col3.subheader("Damage predictors")
    pred_data = get_annots(info_dict, config_dict["display_cols"]["pred"])
    annot_col3.write(pred_data)

    annot_col4.subheader("Function")
    clinical_data = get_annots(info_dict, config_dict["display_cols"]["clinical"])
    annot_col4.write(clinical_data)

    # st.write(info_dict)

    # # initialise data of lists to print on the webpage.
    # var_scores = {
    #     "Source": [
    #         "DITTO score",
    #         "Clinvar Classification",
    #         "Clingen Classification",
    #         "gnomAD AF",
    #     ],
    #     "Values": [
    #         # str(round(1 - (ditto["DITTO"].values[0]), 2)),
    #         str(ditto["DITTO"].values[0]),
    #         ditto["clinvar.sig"].values[0],
    #         ditto["clingen.classification"].values[0],
    #         annots["gnomad3.af"].values[0],
    #     ],
    # }
    # # Create DataFrame
    # col1.dataframe(pd.DataFrame(var_scores))

    # # SHAP explanation
    # shap_value = explainer.shap_values(annots.values)[0]

    # # SHAP explanation plot for a variant
    # col2.pyplot(
    #     shap.plots._waterfall.waterfall_legacy(
    #         1 - explainer.expected_value[0],  # DITTO prediction for deleterious is (1 - y_pred)
    #         np.negative(shap_value[0]),  # SHAP value for deleterious is negative
    #         annots.values[0],
    #         feature_names,
    #         max_display=20,
    #     )
    # )


if __name__ == "__main__":
    main()
