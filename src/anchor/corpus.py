NOTES = [
    (
        "Refunds",
        "A missed pickup is refunded only when the driver marks the stop as missed. The refund window is 5 days from that mark. If the customer was absent, there is no refund.",
    ),
    (
        "On-call",
        "Page the secondary on-call if the primary has not acknowledged within 10 minutes. Do not page the whole channel for one delayed stop.",
    ),
    (
        "Chunking",
        "Support documents are split into 512-token chunks with a 64-token overlap before they are embedded.",
    ),
    (
        "Privacy",
        "Raw phone numbers never go to the model. Redact them before retrieval. Payment card numbers are dropped, not masked.",
    ),
    (
        "Canary",
        "A canary receives 10 percent of traffic for 30 minutes. Roll back if the error rate rises above 0.5 percent.",
    ),
    (
        "Disputes",
        "Support handles billing disputes up to 200 dollars. A dispute over 200 dollars goes to finance, which replies within 2 business days.",
    ),
]
