# GPU Runner Setup for Model Training

This document describes how to set up a self-hosted GPU runner for model training workflows.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- NVIDIA GPU with CUDA support (RTX 3090/4090, A10, A100, etc.)
- Docker installed
- GitHub Actions runner token

## Quick Setup

### 1. Install NVIDIA Drivers and CUDA

```bash
# Add NVIDIA repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-driver-535 nvidia-container-toolkit

# Verify
nvidia-smi
```

### 2. Install GitHub Actions Runner

```bash
# Create runner directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download latest runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (get token from GitHub Settings > Actions > Runners)
./config.sh --url https://github.com/Insightpulseai-net/pulser-agent-framework \
  --token YOUR_TOKEN \
  --labels gpu,self-hosted,linux

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 3. Install Python Dependencies

```bash
# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Create virtual environment for training
python3.11 -m venv /opt/ml-venv
source /opt/ml-venv/bin/activate

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
pip install -r ml/train/requirements.txt
pip install -r ml/eval/requirements.txt
```

## Runner Labels

The workflows expect these labels:

| Label | Description |
|-------|-------------|
| `self-hosted` | Required for all self-hosted runners |
| `gpu` | Has GPU available (default label for training) |
| `linux` | Linux OS |

## Workflow Configuration

Workflows use the `gpu_runner` input to specify which runner to use:

```yaml
jobs:
  train:
    runs-on: [self-hosted, "${{ github.event.inputs.gpu_runner }}"]
```

Default value is `gpu`, so configure your runner with that label.

## Monitoring

### Check GPU Usage

```bash
watch -n 1 nvidia-smi
```

### Check Runner Status

```bash
sudo ./svc.sh status
journalctl -u actions.runner.* -f
```

## Troubleshooting

### CUDA Out of Memory

- Reduce batch size in training config
- Enable gradient checkpointing
- Use 8-bit or 4-bit quantization

### Runner Not Picking Up Jobs

- Check runner is online: `./run.sh` interactively
- Verify labels match workflow requirements
- Check network connectivity

### PyTorch Can't Find CUDA

```bash
# Verify CUDA installation
nvcc --version
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with correct CUDA version
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

## Alternative: Docker-based Training

Instead of installing dependencies on the runner, use a Docker image:

```bash
# Pull training image
docker pull pytorch/pytorch:2.0.0-cuda11.8-cudnn8-runtime

# Run training
docker run --gpus all -v $(pwd):/workspace -w /workspace \
  pytorch/pytorch:2.0.0-cuda11.8-cudnn8-runtime \
  python ml/train/run.py --config configs/sft_lora_1b.yaml --run-id test
```

## Cloud GPU Options

If you don't have local GPU hardware:

- **RunPod**: On-demand GPU instances
- **Lambda Labs**: GPU cloud with good pricing
- **DigitalOcean GPU Droplets**: Managed GPU instances
- **AWS/GCP/Azure**: Enterprise GPU instances

Configure the runner on the cloud instance and add appropriate labels.
