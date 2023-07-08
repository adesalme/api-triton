# Triton Model Gateway

This repo contains a quick and dirty POC API that provides a gateway to NVIDIA's Triton inference server. This gateway can resolve complex 
model dependencies and also supports model versioning with semver (Triton only supports integer versions right now).

### Quickstart
Install the conda env:
```bash
conda env create -f environment.yaml -n triton-model-gateway
```

Start web server:
```bash
conda activate triton-model-gateway
sh scripts/run.sh
```

Start Triton:
```bash
# Get models from here https://github.com/triton-inference-server/server/tree/main/docs/examples and run fetch_models.sh
docker run -d --rm -p8000:8000 -p8001:8001 -p8002:8002 -v model_repository:/models/test:Z nvcr.io/nvidia/tritonserver:23.06-py3 tritonserver --model-repository=/models/test
```

Run benchmark:
```bash
conda activate triton-model-gateway
python3 scripts/benchmark.py  # to see service return values
python3 -O scripts/benchmark.py  # to see throughput
```