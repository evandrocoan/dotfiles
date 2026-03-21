#!/bin/bash

# 1. Find the highest temperature across all sensors
# Use formatted `sensors` output and extract only the first (input) temp per sensor line,
# skipping indented threshold lines (high/crit/hyst etc.)
MAX_TEMP=$(sensors | awk '!/^ / && /°C/ {
    if (match($0, /\+[0-9]+\.[0-9]+/)) {
        val = substr($0, RSTART+1, RLENGTH-1) + 0
        if (val > max) max = val
    }
} END {printf "%.0f", max}')

# 2. Get the full list of temperatures for the hover tooltip
ALL_TEMPS=$(sensors | grep "°C" | sed 's/&/&amp;/g; s/</&lt;/g; s/>/&gt;/g')

# 3. Format the output for the XFCE panel
if [ "$MAX_TEMP" -ge 80 ]; then
    # If it hits 80C or higher, make the text red to warn you!
    echo "<txt><span fgcolor='red'>🔥 ${MAX_TEMP}°C</span></txt>"
else
    # Normal display
    echo "<txt>${MAX_TEMP}°C</txt>"
fi

# 4. Create the hover tooltip
echo "<tool>All System Temperatures:
${ALL_TEMPS}

Sensor key:
  Tctl    - Synthetic AMD CPU temp reported to the cooler; derived from die temps but may include a manufacturer offset to tune fan curves
  Tccd1   - Actual temp of Core Complex Die 1 (one physical chiplet, typically 8 cores)
  Tccd2   - Actual temp of Core Complex Die 2 (second physical chiplet, typically 8 cores); each die is measured separately as they can run at different temps
  temp1   - Motherboard chipset or VRM sensor
  Composite - NVMe SSD worst-case summary; reports whichever internal sensor is highest (used by OS for throttling)
  Sensor 1  - NVMe SSD internal sensor, typically the NAND flash chips
  Sensor 2  - NVMe SSD internal sensor, typically the controller chip</tool>"
