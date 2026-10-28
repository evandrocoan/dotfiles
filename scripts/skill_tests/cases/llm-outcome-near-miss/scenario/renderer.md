# Duplicate publication

The model's recorded response contains one finding with canonical ID `f1` and one explanation.
The canonical application result also contains only `f1`. The renderer copies that explanation
into a summary, a category section, and the detailed finding. All three copies are published.

The requested behavior is a summary count and one detailed explanation per canonical finding.
The model, prompt, candidate selection, permissions, and cost policy are unchanged. The renderer
can be called with a canonical result without contacting a provider; an existing dispatcher replay
also covers this publication path with fixed model responses and blocked network.
