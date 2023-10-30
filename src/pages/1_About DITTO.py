import streamlit as st
from PIL import Image

# Config the whole app
st.set_page_config(
    page_title="DITTO",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


@st.cache_data
def load_ditto_data():
    corr = Image.open("./results/correlation.png")
    roc_overall = Image.open("./results/benchmark.png")
    consq_features = Image.open("./results/shap_consq.png")
    ditto = Image.open("./results/model.png")
    return corr, roc_overall, ditto, consq_features


def main():
    corr, roc_overall, ditto, consq_features = load_ditto_data()
    # intro_col1, intro_col2 = st.columns([2, 1])
    st.subheader("DITTO (Deleterious prediction tool for genetic variants)")
    st.markdown("--------")
    st.write("**Methods:**")
    st.markdown("- DITTO (unpublished) is used to identify likely deleterious variants.")
    st.markdown(
        "- DITTO is an explainable deep learing model that"
        " was built using [Tensorflow](https://www.tensorflow.org/) framework."
    )
    st.markdown(
        "- We downloaded 185,135 reported pathogenic and benign classified variants"
        " or 1,050,826 variant transcript pairs from [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) and"
        " annotated with 130 data scources that relate to variant frequency, impact, and"
        " damage predictions using [OpenCravat](https://opencravat.org/). "
    )
    st.markdown(
        "- These variants were trained through DITTO and evaluated on precision"
        " and accuracy scores. DITTO achieved ~99% accuracy in correctly"
        " predicting the class reported in"
        " [Clinvar](https://www.ncbi.nlm.nih.gov/clinvar/). "
    )
    st.markdown(
        "- DITTO uses [SHAP](https://shap.readthedocs.io/en/latest/index.html)"
        " for explaining predictions for each variant and the model itself."
    )
    st.markdown("--------")
    st.subheader("DITTO Metrics")
    st.markdown(
        "We obtained ~130 annotations from OpenCravat for ~1 million variant-transcripts from"
        " ClinVar. Here's a correlation plot showing the dependancy of"
        " annotations/features used for training DITTO. "
    )
    st.image(corr, caption="Correlation plot")
    st.markdown(
        "We used Neural network architecture from tensorflow framework and trained DITTO on the"
        " above features. Below is a SHAP plot explaining how DITTO learned"
        " from each feature. For example, the top feature shows that DITTO is"
        " influenced to predict a variant as Deleterious if it has"
        " low allele frequency i.e. rare variant and not seen in healthy"
        " population from GnomeAD. The next feature says that if a variant has high CADD score, DITTO predicts this as Deleterious. "
    )
    st.write("**DITTO architechture**")
    st.image(ditto, caption="DITTO Architechture and feature importance.")

    st.markdown("--------")
    st.subheader("Benchmarking DITTO on other predictors overall.")
    st.image(roc_overall)

    st.markdown("--------")
    st.subheader("Feature importance plots by consequence.")
    st.image(consq_features)


if __name__ == "__main__":
    main()
