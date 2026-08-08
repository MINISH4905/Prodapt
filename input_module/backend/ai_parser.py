import re


def parse_idea(idea: str):
    """
    Convert a raw startup idea into a basic structured startup profile.
    Replace this function with an LLM call later.
    """

    text = idea.strip()

    # Basic extraction
    solution = text

    # Try to identify target customers
    customer_patterns = [
        r"for ([^.]+)",
        r"helps ([^.]+)",
        r"helping ([^.]+)"
    ]

    target_customer = "Not specified"

    for pattern in customer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            target_customer = match.group(1).strip()
            break

    return {
        "problem": "Problem identified from startup idea",
        "solution": solution,
        "target_customer": target_customer,
        "business_model": "Not specified",
        "market": "Not specified",
        "assumptions": [
            "Customers have this problem",
            "Customers are willing to use the solution",
            "The solution can be technically implemented"
        ]
    }