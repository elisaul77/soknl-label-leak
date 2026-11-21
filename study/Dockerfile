# Standalone equivalent of the image used for the formal run (same pins). Not itself used for a formal run.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless && rm -rf /var/lib/apt/lists/*
RUN printf 'numpy==1.26.4\nscipy==1.13.1\nscikit-learn==1.4.2\n' > /tmp/c.txt \
 && pip install --no-cache-dir -c /tmp/c.txt torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -c /tmp/c.txt capymoa==0.11.0
# CapyMOA downloads its jar on first use; force it here so runs can go without network.
ENV CAPYMOA_DATASETS_DIR=/tmp/capymoa_data
RUN python3 -c "import capymoa; from capymoa.regressor import AdaptiveRandomForestRegressor, SOKNL; print('capymoa', capymoa.__version__)"
WORKDIR /w
