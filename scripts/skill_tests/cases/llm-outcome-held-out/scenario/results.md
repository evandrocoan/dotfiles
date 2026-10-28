# Evaluation notes

A signed product requirement says that enabling a trust flag must use a fixed route and disable
dynamic route discovery. The new code does exactly that. The old code ignored the flag. A review
labels the removal of dynamic discovery a defect solely because behavior changed. The maintainer
replies that the change is intentional; the signed requirement is independently available.

Another case was labelled clean because the previous reviewer reported no findings. A later
independent reproduction demonstrates a cross-tenant leak in that exact source revision. Both
systems' saved answers remain available, and one reported that leak accurately. The comparison
still counts it as a false positive against the old clean label. No other case was verified clean.

A separate renderer repair passes a deterministic test showing one publication per canonical
finding instead of three. The team combines these observations into the conclusion that the new
model has a lower false-positive rate and that every previously disputed finding was incorrect.
