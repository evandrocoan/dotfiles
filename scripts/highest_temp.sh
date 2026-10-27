#!/usr/bin/env bash
set -euo pipefail

# Capture one sample with a stable decimal separator, preserving errors on stderr.
if ! SENSOR_OUTPUT=$(LC_ALL=C sensors); then
    SENSOR_OUTPUT=''
fi

# 1. Find the highest actual reading, accepting C and °C, signs and integers.
# Require the reading immediately after the label, excluding alarm thresholds.
MAX_TEMP=$(LC_ALL=C awk '
    /^[^:]+:[[:space:]]*[+-]?[0-9]+([.][0-9]+)?[[:space:]]*(°)?C([[:space:]]|$)/ {
        reading = $0
        sub(/^[^:]+:[[:space:]]*/, "", reading)
        val = reading + 0
        if (!found || val > max) max = val
        found = 1
    }
    END {if (found) printf "%.0f", max}
' <<< "$SENSOR_OUTPUT")

# 2. Get the full list of temperatures for the hover tooltip
ALL_TEMPS=$(LC_ALL=C awk '/[0-9][[:space:]]*(°)?C([[:space:])]|$)/' <<< "$SENSOR_OUTPUT" |
    sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')

# 3. Format the output for the XFCE panel
if [ -z "$MAX_TEMP" ]; then
    printf 'Error: No valid temperature readings available from sensors.\n' >&2
    printf '<txt>N/A</txt>\n'
    ALL_TEMPS='No temperature readings available.'
elif [ "$MAX_TEMP" -ge 80 ]; then
    # If it hits 80C or higher, make the text red to warn you!
    echo "<txt><span fgcolor='red'>${MAX_TEMP}°C</span></txt>"
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
