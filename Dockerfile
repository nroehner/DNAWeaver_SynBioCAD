FROM continuumio/miniconda3

ENV PATH="/opt/conda/bin:${PATH}"

WORKDIR /app

COPY . /app

RUN conda install --yes --name base conda-libmamba-solver

RUN conda env create --yes --name dnaweaver --file ./environment.yaml --solver=libmamba

# I/O directory for mounting volume is /app/io_data
RUN mkdir -p ./io_data

CMD ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate dnaweaver && python -m dnaweaver_synbiocad ./io_data/cluster_designs.xml ./io_data/gibson_assembly.xlsx gibson"]
