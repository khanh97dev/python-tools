import subprocess
import time

GPU_NAME = "NVIDIA Quadro M1000M"

# Disable GPU
subprocess.run([
    "powershell",
    "-Command",
    f"Get-PnpDevice -FriendlyName '*{GPU_NAME}*' | Disable-PnpDevice -Confirm:$false"
], shell=True)

# Wait a few seconds
time.sleep(5)

# Enable GPU
subprocess.run([
    "powershell",
    "-Command",
    f"Get-PnpDevice -FriendlyName '*{GPU_NAME}*' | Enable-PnpDevice -Confirm:$false"
], shell=True)
