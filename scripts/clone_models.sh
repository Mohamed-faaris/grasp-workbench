#!/usr/bin/env bash
set -euo pipefail
mkdir -p external
clone() {
  local url="$1" dir="$2"
  if [[ -d "$dir/.git" ]]; then echo "Already cloned: $dir"; else git clone "$url" "$dir"; fi
}
clone https://github.com/skumra/robotic-grasping.git external/robotic-grasping
clone https://github.com/ethz-asl/vgn.git external/vgn
clone https://github.com/NVlabs/contact_graspnet.git external/contact_graspnet
clone https://github.com/graspnet/graspnet-baseline.git external/graspnet-baseline
